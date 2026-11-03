# urban-workflow — contexte projet

## Objectif

Portage Python du moteur de workflow .NET
[Black-Beard-Sdk/Workflow](https://github.com/Black-Beard-Sdk/Workflow)
(machine à états pilotée par un DSL métier), en remplaçant son système de
normalisation des sorties JSON par **urban-json** (package PyPI de l'auteur,
moteur JSLT, repo source `gaelgael5/Jslt`).

**Priorité exprimée par l'utilisateur : la reprise du langage DSL.**

Lire `docs/analyse-portage.md` : analyse complète du projet source, choix
structurants actés, architecture cible et plan en 6 étapes.

## Branche de travail

`claude/jolly-fermi-yesjef` — tout se committe et se pousse là (messages de
commit en français).

## État d'avancement

- [x] **Analyse** — `docs/analyse-portage.md` (inventaire source, remplacement
  urban-json, dépendances, bugs du source à ne pas reproduire §5)
- [x] **Étape 1 — Socle** : `urban_workflow/` (models, values/ContextRef,
  config + builders fluides, registry, clock, constants, exceptions),
  29 tests pytest verts.
- [x] **Étape 2 — DSL** : `urban_workflow/dsl/` (grammaires reprises telles
  quelles dans `grammar/` + `regenerate.sh`, parseur généré ANTLR 4.13.2
  commité dans `generated/`, `WorkflowScriptParser`, `WorkflowConfigVisitor`,
  chargeur `INCLUDE`/`FRAGMENT`), 84 tests verts dont golden README source +
  `ParserUnitTest`.
- [x] **Étape 3 — Moteur** : `urban_workflow/engine/` (factory, processor,
  engine + locks CRC32, chaîne d'append, couture `ActionTranslator`) et
  `urban_workflow/outputs/` (décorateurs + transactions, mémoire), 113 tests
  verts dont ports de `WorkflowsUnitTest` et scénarios DSL bout-en-bout.
- [x] **Étape 4 — Templating urban-json** : `urban_workflow/templating/`
  (`TemplateRegistry` JSLT + fichiers `.jslt`, `MetadataRegistry`,
  `JsltActionTranslator` branché sur la couture `ActionTranslator`,
  document de contexte action/workflow/event/incoming/now), 127 tests verts.
- [ ] **Étape 5 — Persistance SQL** (prochaine) : SQLAlchemy, extra optionnel
- [~] **Étape 6 — Finitions** : documentation française faite —
  `docs/guide-dsl.md` (langage complet), `docs/guide-integration.md`
  (moteur, templates, sorties), `docs/guide-tests.md` (règles et tests),
  README réécrit ; le cas d'usage des guides (circuit de validation) est
  pérennisé dans `tests/test_docs_examples.py` (133 tests verts).
  Reste : CI GitHub Actions, version anglaise des guides éventuelle.

## Étape 2 (DSL) — acquis

- `urban_workflow/dsl/grammar/` : `WorkflowLexer.g4` / `WorkflowParser.g4`
  **inchangées** par rapport au source ; `regenerate.sh` régénère le parseur
  (jar ANTLR 4.13.2 téléchargé depuis Maven Central — www.antlr.org peut être
  bloqué ; même version que le runtime `antlr4-python3-runtime` d'urban-json).
- `urban_workflow/dsl/generated/` : code généré commité, ne jamais l'éditer.
  Particularité cible Python : accesseurs `state_()` et `type_()`.
- `WorkflowScriptParser.parse_string/parse_path` → arbre + `includes`,
  `is_fragment`, `crc`, erreurs de syntaxe positionnées (`check()` →
  `DslSyntaxError`).
- `WorkflowConfigVisitor(rules=FunctionRegistry)` + `add_rule()` fluide ;
  conditions `WHEN` compilées en closures avec log fonctionnel ; arguments
  `'littéral'` convertis au type déclaré, `@chemin` → `ContextRef`, nom nu →
  constante sinon littéral ; validations positionnées (`fichier:ligne:col`) ;
  cibles `SWITCH` vérifiées à la fin du script.
- Bugs du source non reproduits (tests dédiés) : condition inversée de
  `VisitParameters`, arguments `@…` d'action devenus littéraux dans
  `GetLambda`.
- `EXPIRE AFTER` : événement `__expired`, garde `CurrentState`, actions
  techniques push/cancel reminder (délais en **minutes**).

## Étape 3 (Moteur) — acquis

- `engine/factory.py` : `WorkflowFactory` (créateurs par type/nom+version,
  `context_factory` pour sous-classer `RunContext`). **L'événement
  d'historique porte l'uuid de l'événement entrant** — le source générait
  un Guid neuf et sa garde anti-double-intégration ne se déclenchait jamais.
- `engine/serializer.py` : `parse_incoming_event` — propriétés CamelCase
  connues (`Name`, `Uuid`, `ExternalId`, `CreationDate`, `EventDate`) vers
  les champs typés, le reste en `extended_datas`.
- `engine/processor.py` : flux complet (existants par ExternalId +
  restriction `WorkflowId`, Initializers + CONCURENCY, transitions,
  récursif, collecte, append, traduction, sorties sous transaction).
  `evaluate_event` retourne les contextes impactés.
- `engine/engine.py` : verrou `zlib.crc32(external_id)` + compteur d'usage ;
  `engine/translator.py` : couture `ActionTranslator` pour l'étape 4,
  `DefaultActionTranslator` matérialise sans template (dont `$_reminder`).
- `outputs/` : `Transaction` context-manager (rollback réel sans commit),
  `MemoryStorage`/`MemoryLocker`, chaîne `default_memory_output(storage)` =
  SetProperties → PushBus → PushModel.
- Écarts assumés vs source (tests dédiés) : garde CONCURENCY stricte (`<`),
  rejeu d'un événement déjà intégré sans recréation de workflow,
  rollback effectif, `Decrement` qui décrémente,
  `create_base_incoming_event` aux conditions remises à l'endroit.

## Étape 4 (Templating urban-json) — acquis

- `templating/context.py` : `build_action_document(ctx, action)` → document
  JSON `action/workflow/event/incoming/now` ; données étendues fusionnées
  dans leur section (clés CamelCase), champs normalisés snake_case
  prioritaires ; `json_safe` (datetime→ISO, UUID→str, Enum→value).
- `templating/registry.py` : `TemplateRegistry` (`add_template`,
  `add_directory` — nom de fichier `.jslt` = nom d'action, `default.jslt` =
  défaut, `functions=` registre urban-json custom) ; constantes
  `DEFAULT_ACTION_TEMPLATE` (même forme que `TemplateModels.DefaultAction` :
  Uuid/Name/PushedAt/Arguments/WorkflowId/EventId/From_State/To_State) et
  `REMINDER_TEMPLATE` (pré-enregistrée sous `$_reminder`, remplaçable).
- `templating/metadata.py` : `MetadataRegistry` — fusion **par clé de
  métadonnée** (bug §5 `AddMetadata` non reproduit), défaut, copies.
- `templating/translator.py` : `JsltActionTranslator(templates, metadatas)`
  → `execute_message = {"Header": dict, "Body": …}` (forme `MessageRaw`),
  encapsulation `$_reminder` des actions différées (corps réel sous
  `Message`). `DefaultActionTranslator` (étape 3) aligné sur la même forme.
- API urban-json utilisée : `JsltTemplate.parse(src).build()`,
  `.transform(doc, functions=…)`, `default_registry.copy()` +
  `register(name, func)` avec convention `func(ctx, *args)` ; chemins
  absents → `None`. Le sous-paquet n'est pas réexporté par la racine
  (comme `dsl`) — import via `urban_workflow.templating`.

## Étape 5 (Persistance SQL) — notes de reprise

1. Recloner le source si absent :
   `git clone --depth 1 https://github.com/Black-Beard-Sdk/workflow /home/user/black-beard-sdk/workflow`
2. Décision actée (analyse §1/§4) : **ne pas porter** le micro-ORM maison
   (`Black.Beard.Workflows.Outputs.Sql`, 37 fichiers) — le remplacer par
   SQLAlchemy Core en extra optionnel `[sql]` (SQLite en dev/tests,
   PostgreSQL en prod). Lire le source seulement pour le **schéma logique**
   (tables workflows/événements/actions poussées) et la sémantique des
   `OutputAction` SQL (upsert modèle, push bus, transaction).
3. Cible : `urban_workflow/storage_sql/` — stockage SQLAlchemy Core
   (workflows sérialisés JSON + index external_id/uuid), `OutputAction`s
   SQL réutilisant `Transaction` (commit/rollback réels sur la connexion),
   et un `Storage` abstrait si utile pour partager l'interface avec
   `MemoryStorage` (get_by external_id = le besoin du processor).
4. `pyproject.toml` : extra `[project.optional-dependencies] sql =
   ["sqlalchemy>=2"]` ; tests d'intégration SQLite en mémoire, skippés
   proprement si sqlalchemy absent.
5. Interface `OutputBus` abstraite seulement (analyse §1, Outputs.Mom) —
   pas d'implémentation broker en v1.

## Commandes

```bash
pip install --break-system-packages -e . pytest   # setup
python3 -m pytest -q                               # tests
```

## Conventions du portage

- Python ≥ 3.10, dataclasses stdlib (pas de pydantic), snake_case ; les noms
  de concepts du source sont conservés (`WorkflowConfig`, `StateConfig`…).
- Les `DynObject` du source = dicts JSON-compatibles ; valeurs paresseuses via
  `values.ContextRef` / callables `(ctx) -> object`, résolues à la traduction.
- Règles métier = callables `(ctx, **kwargs) -> bool` dans `FunctionRegistry`.
- Pas de traduction ligne à ligne : les bugs listés en §5 de l'analyse ne
  doivent pas être reproduits (tests dédiés).
- Sync d'abord, aucun I/O dans le cœur ; horloge via `WorkflowClock.now()`
  uniquement.
