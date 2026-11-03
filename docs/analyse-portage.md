# Analyse de portage — Black-Beard-Sdk/Workflow (.NET) → urban-workflow (Python)

> Analyse du dépôt source `https://github.com/Black-Beard-Sdk/Workflow` en vue de son
> portage en Python, avec remplacement du système de normalisation des sorties JSON
> par [urban-json](https://pypi.org/project/urban-json/) (JSLT).

---

## 1. Inventaire du projet source

| Projet | Taille (.cs) | Rôle | Décision de portage |
|---|---|---|---|
| `Black.Beard.Workflows.Models` | 66 fichiers, ~4 000 l. | **Cœur** : moteur, modèles, configuration, outputs mémoire, templates | **Porter** |
| `Black.beard.Workflow.AntlrParser` | 19 fichiers, ~6 500 l. (dont ~5 000 générées par ANTLR) | Grammaire du DSL + visiteur construisant la config | **Porter** (grammaire réutilisée, visiteur réécrit ≈ 1 300 l.) |
| `Bb.Expressions` | 16 fichiers, ~1 500 l. | Surcouche de `System.Linq.Expressions` (compilation de lambdas) | **Ne pas porter** — inutile en Python (closures) |
| `WorkflowSerializers` | 3 fichiers, ~400 l. | Sérialisation JSON Newtonsoft (DynObject, Message) | **Remplacer** par urban-json + `json` stdlib |
| `Black.Beard.Workflows.Outputs.Sql` | 37 fichiers, ~3 500 l. | Micro-ORM maison + persistance SQL Server | **Remplacer** par SQLAlchemy (extra optionnel) |
| `Black.Beard.Workflows.Outputs.Mom` | 4 fichiers, ~140 l. | Push vers broker de messages | **Interface abstraite** seulement en v1 |
| `UnitTestWorkflow` | 7 fichiers, ~1 100 l. | Tests MSTest de bout en bout | **Porter** en pytest (spécification de référence) |
| `VisualStudioIntegration`, `InstallerLanguageWorkflow` | — | Extension VS, language server, coloration | **Hors périmètre** |

---

## 2. Ce que fait le moteur

### Concepts

- **`WorkflowConfig`** : une machine à états versionnée, déclarée via un DSL dédié
  (`NAME`/`VERSION`, `DEFINE EVENT|RULE|ACTION|CONST`, `INITIALIZE WORKFLOW`,
  `DEFINE STATE … ON EVENT … WHEN … SWITCH …`, `EXPIRE AFTER n DAY`,
  `EXECUTE action(args)`, `STORE (k='v')`).
- **`WorkflowsConfig`** : plusieurs configs chargées ensemble ; le routage d'un
  événement se fait par les filtres `MATCHING (Country = 'France')` et le versionnage.
- **Règles et actions métier** : déclarées dans le DSL (`DEFINE RULE IsMajor(INTEGER agemin)`),
  implémentées côté hôte et enregistrées par nom (`visitor.AddRule("IsMajor", …)`).
  Le visiteur compile les conditions `WHEN` en `Func<RunContext,bool>` via des arbres
  d'expressions ; les arguments `@Event.ExternalId` sont résolus par chemin dans les
  données étendues.

### Flux d'exécution d'un événement

```
payload JSON
  → WorkflowEngine.EvaluateEvent          (lock par ExternalId, clé CRC32)
  → WorkflowProcessor.EvaluateEvent
      1. charge les workflows existants par ExternalId (callback de storage)
      2. évalue la création de nouveaux workflows (Initializers + CONCURENCY)
      3. évalue les transitions : règles WHEN, règles d'entrée/sortie d'état,
         mode récursif ; collecte des ResultAction (EXECUTE / STORE)
      4. TranslateActions : template(nom d'action) + metadata(headers)
         → MessageRaw { Header, Body } → PushedAction accroché à l'événement
      5. chaîne d'OutputAction (décorateurs) sous transaction :
         SetProperties → PushBus → PushModel (persistance)
```

- **Expiration** : `EXPIRE AFTER` produit une action `$_reminder` qui encapsule le
  message réel (bus de rappel différé). Événements techniques : `$_result`,
  `__expired`, `__cancelReminderAction`.
- **`RunContext`** : porte le workflow, l'événement entrant, l'événement créé, les
  actions collectées et le log fonctionnel. C'est l'objet passé aux règles métier.
- Le pattern **chaîne de responsabilité** (`AppendEvents/`) décide où l'événement
  s'insère dans l'arbre du workflow ; le pattern **décorateur + transaction** des
  sorties est sain et sera conservé.

---

## 3. Le système de sortie actuel — et son remplacement par urban-json

### Aujourd'hui (la partie « compliquée » du README)

Pour produire le JSON d'une action poussée, le code traverse **cinq représentations** :

```
TemplateRepository (lambdas C# enregistrées par RÉFLEXION sur des classes statiques)
  → DynObject        (arbre JSON paresseux, feuilles Func<RunContext, object>)
  → .Resolve(ctx)    → arbre Message / MessageBlock / MessageProperty / MessageValue
  → MessageVisitor   → Newtonsoft JToken
  → string JSON
```

soit ≈ 1 100 lignes (DynObject 390, Messages ~160, Templates ~210, serializers ~390),
des templates **compilés dans le binaire** (non modifiables sans redéploiement), et
une duplication DynObject/Message qui n'existe que pour séparer « défini » et « résolu ».

### Demain avec urban-json

urban-json est un moteur JSLT complet (JSONPath, opérateurs, `when`/`switch`, boucles,
fonctions custom enregistrables). Le remplacement :

1. **Un document source par action** — le contexte sérialisé une fois en JSON :

```json
{
  "action":   { "uuid": "…", "name": "Cut", "arguments": { "key": "…" } },
  "workflow": { "uuid": "…", "name": "wrk1", "external_id": "…", "state": "State1" },
  "event":    { "uuid": "…", "name": "Event1", "from_state": "…", "to_state": "…" },
  "incoming": { "…": "données étendues de l'événement entrant" },
  "now":      "2026-11-03T10:00:00Z"
}
```

2. **Un template JSLT par nom d'action** (fichiers `.jslt` dans un répertoire,
   plus un template par défaut — l'équivalent de `TemplateModels.DefaultAction`) :

```jslt
{
  "Uuid":        $.action.uuid,
  "Name":        $.action.name,
  "PushedAt":    $.now,
  "Arguments":   $.action.arguments,
  "WorkflowId":  $.workflow.uuid,
  "EventId":     $.event.uuid,
  "From_State":  $.event.from_state,
  "To_State":    $.event.to_state,
  "ExternalId":  $.workflow.external_id,
  "EventDate":   $.incoming.event_date
}
```

3. Un `TemplateRegistry` (~100 lignes) : résolution nom d'action → template,
   fallback défaut, en-têtes (métadonnées) en simple dict ou second template.

**Gains** : `DynObject`, `Message*`, `MessageVisitor`, les trois serializers et les
deux repositories à réflexion disparaissent ; les templates deviennent des fichiers
déclaratifs, modifiables sans redéployer, testables en triplets
*template → entrée → sortie* (exactement le format de la suite de tests d'urban-json).

---

## 4. Dépendances .NET et équivalents Python

⚠️ Le dépôt source **ne compile pas seul** : `Black.Beard.Workflows.Models` et
`Outputs.Sql` référencent en `ProjectReference` relatifs (`..\..\..`) deux **dépôts
frères** attendus à côté du clone : `Black.Beard.Expressions` et
`Black.Beard.ComponentModel`. Pour le portage, on n'en a pas besoin : leur usage
(compilation d'expressions, accesseurs par réflexion) se remplace par des idiomes
Python. À noter : `Src/Bb.Expressions` existe aussi en copie locale dans le dépôt,
mais c'est la copie externe qui est référencée — la locale semble être un vestige.

| Dépendance .NET | Rôle | Équivalent Python |
|---|---|---|
| `Antlr4.Runtime.Standard` 4.7.2 | Runtime du parseur DSL | `antlr4-python3-runtime` 4.13.2 — **déjà la dépendance d'urban-json**, aucune dépendance nouvelle |
| `Newtonsoft.Json` | JSON | `json` stdlib + urban-json |
| `Ude.NetStandard` | Détection d'encodage des fichiers DSL | Lire en UTF-8 (suffisant ; `charset-normalizer` si vraiment nécessaire) |
| `Black.Beard.Expressions` (repo frère) | Arbres d'expressions compilés | Inutile — closures et callables |
| `Black.Beard.ComponentModel` (repo frère) | Réflexion / accesseurs | Inutile — `getattr`, dataclasses |
| `Black.Beard.Brokers.Contracts` | Contrats MOM (bus) | Interface abstraite `OutputBus` (implémentations concrètes hors cœur) |
| `System.Data.SqlClient` + micro-ORM `Dao/` maison | Persistance SQL Server | SQLAlchemy Core (SQLite en dev, PostgreSQL en prod) — extra optionnel |
| `Crc2.cs` (CRC32 maison) | Clé de verrouillage | `zlib.crc32` |
| `Interlocked` / locks maison | Concurrence | `threading.Lock` par clé |

---

## 5. Bugs du source à ne pas reproduire

Le portage ne doit pas être une traduction ligne à ligne — plusieurs bugs repérés :

- `WorkflowEngine.UseResource.Decrement()` appelle `Interlocked.Increment` :
  le compteur ne décrémente jamais, `CanBeRemoved` est cassé.
- `WorkflowFactory.CreateBaseIncomingEvent` : la condition
  `if (string.IsNullOrEmpty(incominType))` et le `if (!TryGetValue…)` sont inversés —
  le chemin « type nommé » lèverait une `NullReferenceException`.
- `DynObject.Add(string, string)` : les branches `ContainsKey` sont inversées
  (`Add` quand la clé existe déjà → exception).
- `MetadatRepository.AddMetadata` : utilise `key` (le nom du template) au lieu de
  `metadata.Key` dans le dictionnaire interne — les métadonnées s'écrasent entre elles.

Les tests Python couvriront explicitement ces cas.

---

## 6. Focus — le DSL, priorité du portage

Le langage dédié est la pièce maîtresse à reprendre. État des lieux côté source :

- **La grammaire est la spécification** : `WorkflowLexer.g4` et `WorkflowParser.g4`
  (`Src/Black.beard.Workflow.AntlrParser/Parser/Grammar/`). Mots-clés SQL-like,
  commentaires `--` et `/* */`, chaînes `'…'`, identifiants, `@chemin.composé`,
  délais `2 DAY|HOUR|MINUTE`. Deux points d'entrée : `script_full` (un workflow
  complet) et `script_fragment` (fragment réutilisable via `INCLUDE`).
- **Le code généré** (`WorkflowLexer.cs`, `WorkflowParser.cs`, ~5 000 lignes) ne se
  porte pas : il se **régénère** depuis les `.g4` avec la cible Python 3.
- **Le vrai travail est le visiteur** `WorkflowConfigVisitor` (1 292 lignes) qui :
  1. collecte les déclarations (`DEFINE EVENT/RULE/ACTION/CONST`) et **valide tout à
     la construction** : action/règle utilisée mais non déclarée, arguments nommés
     vérifiés contre la signature déclarée (`INTEGER agemin`…), doublons, états cibles
     des `SWITCH` existants — avec erreurs positionnées (fichier, ligne, colonne) ;
  2. résout les constantes et les chemins `@Event.X` / arguments composés en accès
     paresseux aux données du contexte ;
  3. compile les conditions `WHEN` (arbre NOT/AND/OR de `rule(args)`) en
     `Func<RunContext,bool>` via des arbres d'expressions, en liant chaque appel de
     règle à la méthode C# enregistrée par `AddRule(name, method)`.

### Transposition Python

| Source | Cible Python |
|---|---|
| `.g4` (lexer + parser) | **copiés tels quels**, régénérés avec ANTLR 4.13 cible Python 3 (le runtime est déjà celui d'urban-json ; les grammaires 4.7 se régénèrent sans modification) |
| Code généré C# | code généré Python (commité, régénérable par script) |
| `WorkflowConfigVisitor` | réécriture sur la base `WorkflowParserVisitor` générée — c'est le gros morceau du portage DSL |
| Compilation `WHEN` en arbres d'expressions | **composition de closures** : `rule(args)` → lookup dans le registre + résolution paresseuse des arguments ; `NOT/AND/OR` → combinateurs (`lambda ctx: a(ctx) and b(ctx)`) — mêmes sémantiques, zéro machinerie |
| `AddRule(name, MethodInfo)` | registre de callables `(ctx, **kwargs) -> bool` avec introspection `inspect.signature` pour valider les arguments déclarés |
| `Ude` (détection d'encodage des fichiers inclus) | UTF-8 par défaut |

**Critère de réussite : compatibilité à 100 % des scripts existants.** Tests golden :
l'exemple complet du README source et les cas de `ParserUnitTest` doivent produire une
config équivalente (mêmes états, transitions, règles, actions, erreurs aux mêmes
positions). La conservation du diagnostic positionné (ligne/colonne) fait partie du
contrat — c'est ce qui rend le DSL utilisable.

---

## 7. Architecture Python cible

```
urban_workflow/
  __init__.py
  models.py            # dataclasses : Workflow, Event, IncomingEvent, ResultAction,
                       #               PushedAction, ChangeEnum
  config/              # WorkflowConfig, StateConfig, TransitionConfig,
                       #   IncomingEventConfig, InitializationConfig, WorkflowsConfig
                       # + builder fluide (utilisé par les tests, comme dans le source)
  registry.py          # registre des rules/actions métier : @rules.register("IsMajor")
  dsl/                 # grammaire ANTLR (g4 reprises du source) + visiteur → WorkflowConfig
  engine/              # WorkflowEngine (locks par clé), WorkflowProcessor, RunContext,
                       #   chaîne d'append d'événements, horloge injectable (WorkflowClock)
  outputs/             # OutputAction (chaîne décorateur), ITransaction, MemoryStorage,
                       #   interfaces Storage / OutputBus
  templating/          # TemplateRegistry sur urban-json : contexte JSON, templates .jslt,
                       #   headers/métadonnées, template $_reminder
  storage_sql/         # SQLAlchemy — extra optionnel [sql]
tests/
pyproject.toml         # dépendance : urban-json (qui apporte antlr4-python3-runtime)
```

### Choix structurants (recommandés)

1. **Parseur DSL : ANTLR, grammaires `.g4` reprises telles quelles** (cible Python 3,
   runtime 4.13 déjà requis par urban-json). La grammaire reste la spécification
   unique du langage → compatibilité totale des scripts existants, cohérence
   d'outillage avec urban-json. L'alternative Lark imposerait de réécrire la
   grammaire avec un risque de divergence.
2. **Règles/actions : registre de callables** `(ctx, **kwargs) -> bool` — remplace
   toute la machinerie `MethodReference` + compilation d'expressions.
3. **Modèles : dataclasses stdlib**, pas de pydantic — le cœur reste sans dépendance ;
   la validation vit dans le visiteur DSL (comme dans le source).
4. **Concurrence : sync d'abord**, lock en mémoire par `zlib.crc32(external_id)`
   comme l'original ; aucun I/O dans le cœur du moteur pour permettre un adaptateur
   asyncio plus tard sans refonte.
5. **Sorties : conserver décorateur + transaction**, avec `MemoryStorage` de
   référence pour les tests.

---

## 8. Plan de portage

Le DSL étant la priorité, il vient immédiatement après le socle (le visiteur a
besoin du modèle de config comme cible de construction, mais pas du moteur).

| Étape | Contenu | Validation |
|---|---|---|
| 1. Socle | packaging, `models`, `config` + builder fluide, registre rules/actions | tests unitaires de construction |
| 2. **DSL** | grammaires `.g4` reprises et régénérées en Python, visiteur → `WorkflowConfig`, erreurs positionnées, `INCLUDE`/fragments | port de `ParserUnitTest` + golden test sur l'exemple complet du README source |
| 3. Moteur | processor (création, transitions, règles, collecte d'actions), engine + locks, horloge injectable | port de `WorkflowsUnitTest`, puis scénarios de bout en bout *script DSL → événements → états* |
| 4. Templating | contexte JSON, `TemplateRegistry` urban-json, templates par défaut et `$_reminder`, `TranslateActions` | tests de sortie en triplets template→entrée→sortie |
| 5. Persistance | `storage_sql` SQLAlchemy, interface `OutputBus` | tests d'intégration SQLite |
| 6. Finitions | docs du langage (grammaire + exemples), CI, publication PyPI éventuelle | — |

L'étape 2 (visiteur, ~1 300 lignes à réécrire) est la plus exigeante, mais la
grammaire reprise à l'identique borne le risque ; dès l'étape 3 on a un moteur
pilotable par scripts DSL, ce qui est le cœur de la valeur du projet.
