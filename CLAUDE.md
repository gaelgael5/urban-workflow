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
- [x] **Étape 5 — Persistance SQL** : `urban_workflow/storage_sql/` (extra
  `[sql]`, SQLAlchemy Core — schéma logique du source en 3 tables,
  agrégats JSON, upserts idempotents, chaîne `sql_output` sous transaction
  SQL unique) + interface `OutputBus`/`BusOutputAction` dans `outputs/`,
  141 tests verts (SQLite en mémoire, skip propre sans sqlalchemy).
- [x] **Étape 6 — Finitions** : guides français (`docs/guide-*.md`) et
  anglais (`docs/en/*-guide.md`), README, cas d'usage des guides pérennisé
  dans `tests/test_docs_examples.py` ; CI GitHub Actions
  (`.github/workflows/ci.yml` : tests 3.10→3.13, job sans sqlalchemy pour
  vérifier le skip de l'extra `[sql]`, lint ruff) ; annotations modernisées
  (PEP 585/604) et règles ruff **explicites** dans pyproject
  (`[tool.ruff.lint] select` — les défauts de ruff changent entre
  versions). 141 tests verts. Publication PyPI : non faite, à la demande.

**Le plan en 6 étapes est terminé.** Reprises possibles : publication
PyPI (trusted publisher OIDC), verrou distribué (`LockObject` SQL/Redis),
adaptateur asyncio, fusion des initialiseurs DSL multi-branches.

## Hors plan — Publication PyPI (demandée ensuite)

- Deux distributions : `urban-workflow` (racine) et
  `urban-workflow-playground` (sous-projet `playground/` avec son propre
  `pyproject.toml` ; paquet importable renommé `urban_workflow_playground`,
  script console `urban-workflow-playground`). Les deux noms étaient
  libres sur PyPI (vérifié).
- **Un workflow de release par paquet** (PyPI n'accepte pas deux pending
  publishers identiques, et c'est un meilleur cloisonnement) :
  `release-core.yml` (tag `v*`, environment `pypi`) et
  `release-playground.yml` (tag `playground-v*`, environment
  `pypi-playground`), trusted publishing OIDC, garde tag ↔ version.
  Procédure complète (pending publishers côté pypi.org — seule action à
  la main de l'utilisateur) : `docs/publication-pypi.md`.
- Wheels vérifiées : parseur ANTLR généré inclus côté socle, `static/`
  + vendor inclus côté playground (`[tool.setuptools.package-data]`),
  installation + fumée testées dans un venv vierge
  (`--find-links dist`). `conftest.py` racine ajoute `playground/` au
  `sys.path` ; la CI installe `-e ./playground` dans la matrice.
- L'idée de « paquets par pays » a été abandonnée par l'utilisateur
  (mauvaise conversation) — ne pas la relancer.

## Hors plan — Playground web (demandé ensuite)

- `playground/` (sous-projet, distribution `urban-workflow-playground` ;
  `python -m urban_workflow_playground` → port 8777) : éditeur
  CodeMirror 5.65.18 **vendorisé** (`static/vendor/`, récupéré via le
  tarball npm — cdnjs bloqué par le proxy), mode DSL, **intellisense
  contextuelle** (événements/états/règles/actions/chemins `@`/constantes
  selon le texte avant le curseur, pas dans les chaînes/commentaires),
  lint asynchrone branché sur `POST /api/analyze`.
- `playground/app.py` : `/api/analyze` → erreurs positionnées (syntaxe en
  bloc ; sémantique une par une, position re-parsée du message
  `fichier:ligne:col`) + symboles (visiteur si script valide, repli regex
  sinon) + résumé structurel ; `/api/simulate` → vrai moteur mémoire,
  étapes avec états/actions/journal. Les règles du panneau de paramétrage
  deviennent des callables à signature exacte (identifiants filtrés).
- `conftest.py` racine (rend `playground` importable des tests) ;
  `tests/test_playground.py` (TestClient, skip sans fastapi) ; job CI
  « sans sqlalchemy » couvre aussi ce skip ; lint CI étendu à
  `playground` et `conftest.py`.

## Hors plan — Schémas d'événements (terminé)

- **Première extension assumée de la grammaire** (commentée dans les .g4) :
  `DEFINE EVENT nom 'libellé' AS @nom_schema;` — token `AS` ajouté au lexer,
  `(AS schemaRef=compositekey)?` dans `event_declaration_statement`.
  Parseur régénéré. `AS` devient un mot réservé.
- Les schémas sont **séparés du DSL** (exigence utilisateur) : JSON Schema
  écrits en YAML, chargés à l'initialisation du moteur dans
  `urban_workflow/schemas.py` → `SchemaRegistry` (`add_file`/`add_yaml`/
  `add_directory`/`add_schema`), socle commun `BASE_EVENT_SCHEMA`
  (Name requis, Uuid/dates avec formats) toujours validé en plus du schéma
  métier (`include_base`). Extra optionnel `[schemas]` = PyYAML + jsonschema
  (imports paresseux ; le cœur reste léger).
- Visiteur : param `schemas=None` — sans registre, la référence `AS` est
  **stockée sans résolution** (mode permissif, le playground continue de
  marcher) ; avec registre, référence inconnue = `UnknownSchemaError`
  positionnée, et `DeclaredEventConfig.schema`/`dedup_keys` sont résolus.
  `parse_config(..., schemas=...)` ; `event_to_document` dans
  `engine/serializer.py` (format fil CamelCase pour validation + hash).
- **Anti-doublon : décision utilisateur = A+B, implémenté.** `x-dedup`
  retiré (schémas = JSON Schema pur). A) extension DSL
  `UNIQUE (Prop, …)` sur DEFINE EVENT (token `UNIQUE` + règle
  `unique_keys`, doublon de propriété = erreur positionnée) →
  `DeclaredEventConfig.dedup_keys`, pur DSL (marche sans registre).
  B) propriété réservée `DedupKey` du socle (champ typé
  `IncomingEvent.dedup_key`, mappée dans `_KNOWN_FIELDS`, dans
  `BASE_EVENT_SCHEMA`) — **prioritaire sur UNIQUE**.
  Moteur : `processor._event_gate(config, event)` → valide (socle +
  schéma métier, `EventSchemaError`) et retourne l'empreinte SHA-256 ;
  `_already_integrated` = rejeu Uuid OU même `Event.dedup_hash` dans
  l'historique → ignoré silencieusement (existants ET création).
  Colonne SQL `workflow_events.dedup_hash`. La validation ne s'applique
  que si l'événement serait réellement traité par la config.
- **`IntegrationDate`** (socle, `readOnly`) : posée par `evaluate_event`
  (`WorkflowClock`, avant validation, seulement si absente) ; ignorée si
  l'émetteur l'envoie (`_SYSTEM_FIELDS` du serializer). Portée par
  `IncomingEvent`/`Event.integration_date`, colonne SQL, contexte des
  templates. `Event.creation_date` reste « now » à l'historisation (héritage
  du source, non modifié).
- **Playground à jour schémas/UNIQUE** : panneau « Schémas d'événements »
  dans Paramétrage (nom + YAML, localStorage `uw-playground-schemas`),
  `schemas: [{name, yaml}]` envoyé à `/api/analyze` et `/api/simulate`
  (`_build_schema_registry` — YAML invalide/extra manquant = erreur
  globale propre), visiteur branché avec `schemas=`, symboles enrichis
  (`schemas`, `event_details`, `payload_properties` pour l'intellisense
  `AS @…` et `UNIQUE (…)`), badges AS/UNIQUE dans Structure, exemple
  « validation » avec schéma + doublon `DedupKey` démontrant l'anti-doublon.
  Deps du sous-projet : PyYAML + jsonschema (toujours actifs côté
  playground). `tests/test_playground.py::TestSchemasInPlayground`.
- Jar ANTLR : Maven Central rate-limite parfois (429) — miroir qui marche :
  `maven-central.storage-download.googleapis.com/maven2/...`.

## Hors plan — Vue diagramme du playground (fait)

- `urban_workflow/dsl/surface.py` : **modèle de surface** sérialisable
  (états/transitions/déclarations, gardes et blocs EXECUTE/STORE en texte
  source brut, `_snippet` désindente les continuations) + `render_script`
  canonique. Point fixe testé `render(extract(render(m))) == render(m)` +
  équivalence sémantique via `parse_config`. FRAGMENT/INCLUDE →
  `SurfaceError`. **Le moteur exige un SWITCH sur chaque branche**
  (build résout toutes les cibles) — branche sans SWITCH = boucle
  pointillée dans le diagramme, erreur à l'analyse.
- Playground : `POST /api/diagram` (script → modèle, erreurs
  positionnées) et `POST /api/generate` (modèle → script canonique +
  diagnostics de l'analyse réelle, réutilise `analyze()`).
- Front `static/diagram.js` : bascule Éditeur/Diagramme au-dessus de
  l'éditeur, X6 3.1.8 vendorisé (`static/vendor/x6.min.js`, version
  **ASCII-safe** du prototype — l'original contient des U+00A0 bruts),
  nœuds états (textWrap), arêtes transitions/initialiseurs/expirations,
  ordinaux ①② = priorité des branches, inspecteur flottant (événement
  avec datalist, WHEN, EXECUTE/STORE, SWITCH, ↑↓ priorité, RECURSIVE),
  « Relier » = drag magnétique, « Réorganiser » = BFS en couches,
  positions hors du DSL (voir « Mise en page du diagramme »), événements utilisés
  non déclarés auto-déclarés à la génération. Pont
  `window.PlaygroundBridge` exposé par app.js ; poignée de test
  `window.PlaygroundDiagram`.
- **Piège X6 contourné** : une sélection active (attrs modifiés par le
  highlight) casse la recherche de cible du drag magnétique → entrer en
  mode Relier désélectionne, les clics n'y sélectionnent pas, et la
  création d'un lien sort du mode Relier en sélectionnant la nouvelle
  branche. Tests Playwright : drags au rythme réel (pauses entre
  mousemove), clic des labels d'arêtes par coordonnées (le rect de fond
  intercepte).

## Hors plan — Mise en page du diagramme (fait, 2026-11-07)

- Positions par nom d'état dans `<workflow>.layout.json`
  (`{"version":1,"workflow":…,"states":{Etat:{x,y}}}`), jamais dans le DSL.
  `urban_workflow_playground/layout.py` (`LayoutDirectory`,
  `normalize_layout` : nom de workflow = identifiant sans `..`, x/y finis,
  écriture atomique). Routes `GET/PUT /api/layout/{workflow}`, actives si
  `PLAYGROUND_LAYOUT_DIR` (lu à chaque requête) ; image : `/data/layouts`
  + volume nommé `layouts` dans le compose.
- Front `diagram.js` : store `{load → Promise, save}` remplaçable
  (`PlaygroundDiagram.setLayoutStore`, `reload`) ; défaut = serveur si
  `enabled`, sinon localStorage. `placeMissing()` ne place que les états
  sans position (avant : un seul manquant ré-étalait tout).
- Vue Scripts : `RULE_FUNCTIONS` typées (`params`, `returns`, `doc`,
  `signature`), complétion qui se rouvre après une fonction / `@…​.` /
  `IN (` (`item.reopen` + événement `pick`), bandeau de signature
  (`enclosingCall`).

## Hors plan — États modélisés, `@state`, `@IncomingEvent` (fait)

Cadrage du 2026-11-05 — **trois objets** : l'événement entrant
(`@IncomingEvent`, point d'intégration), l'**état** (créé au SWITCH ; le
calcul de ses champs métier est À CADRER), le workflow (hors cadrage).
- **`$.` supprimé** → `@IncomingEvent.…` (le `@` est collé à la référence),
  mêmes capacités. Grammaire : règle `contextPath` (`AROBASE key
  jsonPathSegment*`) placée AVANT `compositekey` dans `argumentValue` (sur
  un chemin à points, ambigu, ANTLR prend la première alternative) ; token
  `DOLLAR` retiré. `[n]`/`['x']` refusés hors `@IncomingEvent`/`@state`.
  Racines insensibles à la casse. `@Event.…` (historique) reste résolu mais
  n'est plus proposé.
- **FromState/ToState ne sont PAS des propriétés de l'événement** (un même
  événement peut être traité par plusieurs workflows en parallèle) : hors
  du modèle exposé ; l'instance d'état porte **`EventId`** (l'événement qui
  l'a créée). `Event.from_state/to_state` internes (par workflow) restent.
- États : `DEFINE STATE X 'l' AS @schema` ; `BASE_STATE_SCHEMA` = `Name`,
  `Uuid`, `CreationDate`, `EventId` (readOnly). `StateInstance` créée à
  **chaque SWITCH** (même vers l'état courant), d'abord dans
  `ctx.pending_states` (les règles RECURSIVE voient déjà `@state.Uuid`),
  versée dans `workflow.states` par `AppendStandardEvent` ; table SQL
  `workflow_states`.
- `@state` = `StatePath` liée au chargement au NOM de l'état du bloc
  (`_current_state` du visiteur) → instance la plus récente de cet état ;
  erreur positionnée dans INITIALIZE. Contrôle contre le schéma de l'état.
- **Switch viable — TOUT switch, avec ou sans RECURSIVE** (décision
  utilisateur) : `_find_route` ; état cible qui gère l'événement sans
  branche passante → comme si le switch n'avait pas été rencontré (pas
  d'instance ni d'action, état courant conservé ou pas de workflow, branche
  suivante essayée). Route suivie seulement avec RECURSIVE (présélectionnée,
  gardes évaluées une fois) ; regard à un niveau.
- Playground : `models.js` = UN composant pour les vues Événements et États
  (`OBJECT_KINDS`), éléments repérés par `data-ref` scopés à la vue (deux
  vues dans la page) ; `state_details`/`state_properties`/`base_state_paths`
  + repli regex `state_schema_refs` ; contrôle « pas de redéfinition du
  socle » selon l'USAGE du schéma (événement ou état), après le parse.

## Hors plan — Règles : méthodes référencées `AS @script` (fait)

Cadrage du 2026-11-05 (langage complet dès la v1, coexistence Python) puis
**décision du 2026-11-07 : pas de code dans le document de workflow** —
le corps en ligne `AS <expression>` a été SUPPRIMÉ.
- Grammaire : `RULE … comment? (AS scriptRef=compositekey)?` et idem sur
  `ACTION` ; entrée `rule_script : expression SEMICOLON? EOF` pour les
  fichiers de script. Règle `expression` récursive à gauche (priorité =
  ordre des alternatives) ; tokens `IN IS NULL TRUE FALSE` + opérateurs.
- `urban_workflow/scripts.py` : `ScriptRegistry` (`add_script`,
  `add_function`, `add_file` — langage par extension —, `add_directory`,
  `register_language`, `compile`), `ScriptLanguage` (`check` à
  l'enregistrement, `compile(script, ScriptBinding)` à chaque site
  d'appel), `PythonLanguage` (signature contrôlée via `FunctionRegistry`),
  `UnknownScriptError`. `ExpressionLanguage` (`.expr`) dans
  `dsl/expressions.py` (import paresseux depuis le registre : le DSL
  importe `scripts`). `FUNCTIONS` (NOW, LENGTH, CONTAINS, *_BETWEEN) —
  miroir `RULE_FUNCTIONS` dans `static/app.js`. Sémantique « jamais
  d'exception ».
- Visiteur (`scripts=`) : `DeclaredFunction.script_ref` ; référence
  inconnue = erreur positionnée sur `AS @…` ; script + fonction de code
  homonyme = erreur ; `_check_rule_scripts` après TOUTES les déclarations
  (« … (in rule X declared at …) ») puis recompilation à chaque appel
  (« … (called at …) ») ; erreurs positionnées DANS le script
  (`origine:ligne:col`, `make_path(..., error=)`). Sans registre :
  références gardées, appel refusé. Actions : référence vérifiée,
  exécution À CADRER.
- Surface : `SurfaceFunction.script`, rendu `… 'libellé' AS @nom;`.
- Playground : vue **Scripts** (`static/scripts.js`, `#sc-list`/
  `#sc-detail`), scripts en localStorage `uw-playground-scripts` envoyés
  en `scripts: [{name, language, source}]` à analyze/simulate/generate ;
  `_build_script_registry` (toujours un registre ; script en erreur de
  syntaxe remplacé par le langage `invalide` pour ne pas créer de faux
  « script inconnu ») ; erreurs avec champ `script` + doublon dans
  l'éditeur au site d'appel/déclaration (`_CALLED_AT`) ;
  `symbols.rules[].script`, `symbols.scripts` ; complétion `AS @` →
  scripts après DEFINE RULE/ACTION ; « écrire en script » ajoute
  `AS @nom` ; exemples avec `scripts`.
- Docs : `docs/guide-regles.md` (+ `docs/en/rules-guide.md`).
- **Exemples Python (2026-11-08, choix utilisateur : pas de nouveau
  langage)** : `playground/.../python_scripts.py` = fonctions enregistrées
  par le SERVEUR (`add_function`) — `iban_valide`, `email_valide`,
  `jours_ouvres_depuis` — publiées dans `symbols.python_scripts` (source,
  params) et montrées en lecture seule dans la vue Scripts. Le navigateur
  n'envoie que de l'`expression` (autre langage = erreur, avant : 500) ;
  noms Python réservés. Exemple « Scripts Python » (`OuvertureCompte`).

## Hors plan — Arguments `$.chemin` (remplacé par `@IncomingEvent.`)

- **Troisième extension de grammaire** (commentée dans les .g4) : tokens
  `DOLLAR`/`LEFT_BRACKET`/`RIGHT_BRACKET`, règle `jsonPath` dans
  `argumentValue` → `$.Prop`, `$.Liste[0].X`, `$['nom']`, `$` seul.
  Parseur régénéré dans un conteneur `eclipse-temurin:21-jre` sur test1
  (pas de Java sur le poste), jar via le miroir Maven.
- `values.EventPath` (callable comme `ContextRef`) : résolu contre
  `event_to_document(ctx.incoming_event)` (socle + payload) ; absent →
  `None` ; pas de conversion de type. Vaut pour règles ET actions.
- Visiteur : `_current_event` = événement du bloc `ON EVENT`/initialiseur
  en cours ; `_check_event_path` refuse un chemin inconnu du schéma de cet
  événement (si registre fourni), arrêt silencieux sur `$ref`,
  combinaisons, `patternProperties`, `additionalProperties` schéma.
- Playground : `event_properties` (chemins aplatis + type, par événement)
  et `base_paths` dans `/api/analyze` ; le repli regex lit aussi les
  `AS @…` (`schema_refs`) — sinon l'intellisense perd le schéma pendant la
  frappe, quand le script ne compile pas. Complétion après `$` selon le
  dernier `ON EVENT X` avant le curseur (socle seul après `DEFINE STATE`,
  `ON ENTER/EXIT`, `EXPIRE AFTER`).

## Hors plan — Vue Événements du playground (fait)

- Troisième vue (Éditeur | Diagramme | **Événements**) : liste des
  événements du script, détail = **socle en lecture seule** (instance
  `readOnly`, servi par `GET /api/base-event-schema` — source unique
  `BASE_EVENT_SCHEMA`) + **schéma métier** éditable, synchronisé avec son
  YAML et le panneau Paramétrage (même stockage `schemaSettings`).
  « Créer le schéma métier » insère `AS @schema_<Event>` ; « Déclarer »
  ajoute un `DEFINE EVENT` (insertions CodeMirror annulables).
- Composant **réutilisé de Miles** : `SchemaFieldsEditor` de
  jsonjoy-builder (fork vendu, tgz identique à
  `Miles/portail/frontend/vendor/`). Bundle navigateur **commité**
  `static/vendor/schema-editor.{js,css}`, sources dans
  `playground/schema-editor/` (`npm ci && npm run build`, esbuild IIFE,
  `window.UWSchemaEditor`). Le fork ne verrouille pas un champ isolé →
  deux instances. Exclu de l'image (`.dockerignore`).
- CSS : les styles jsonjoy sont en `@layer` → toute règle globale non
  rangée en couche les écrase ; les règles `button, select` du playground
  sont en `:where(…):where(:not(.jsonjoy, .jsonjoy *))` (spécificité
  nulle). Thème = variables `--jsonjoy-*` redéfinies sur `.jsonjoy`
  (s'applique aussi aux dialogues en portail sur `<body>`).
- Serveur : `event_details` liste tous les événements métier (+ `label`,
  `declared`) ; un schéma métier qui redéfinit un champ du socle est
  refusé à l'analyse.

## Hors plan — Livraison sur machine de test (fait)

- Standard « machines de test » : push sur **`dev`** (branche créée depuis
  la branche de travail, à resynchroniser à chaque livraison), puis
  `./dev-deploy.sh` dans le clone `~/urban-workflow` de la machine, puis
  lecture des journaux réels. Aucune retouche manuelle de la cible.
- `playground/Dockerfile` (contexte = racine ; socle `[schemas]` +
  playground installés depuis les sources, non root, HEALTHCHECK sur
  `GET /healthz`), `docker-compose.yml` (stack/port via `.env`),
  `dev-deploy.sh` (9 étapes, pas de migration : pas de base),
  `scripts/declarer-exposition.sh` (copie du script du portail — à
  resynchroniser, pas à faire diverger).
- Ressources : `ia_instructions/tests_and_ressources.md` (`test1` =
  `host-test-37`, port 8777).
- Poste de dev : pas de clé SSH GitHub → pousser en HTTPS
  (`git push https://github.com/gaelgael5/urban-workflow.git …`). Le
  helper global (`devpod agent git-credentials`) a renvoyé des 500 ; le
  script du portail marche : `git -c credential.helper=
  -c credential.helper=$HOME/.config/portal/git-credential-portal.sh push …`.
  Pas de pip local : tests via un conteneur `python:3.12-slim` jetable sur
  la machine de test.

## Étape 2 (DSL) — acquis

- `urban_workflow/dsl/grammar/` : `WorkflowLexer.g4` / `WorkflowParser.g4`
  reprises du source **+ extension `AS` ci-dessus** ; `regenerate.sh`
  régénère le parseur (jar ANTLR 4.13.2 — même version que le runtime
  `antlr4-python3-runtime` d'urban-json).
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

## Étape 5 (Persistance SQL) — acquis

- `storage_sql/schema.py` : tables `workflows` / `workflow_events` /
  `workflow_actions` (schéma logique du `Sqlserver.txt` source ; dates en
  ISO 8601 pour garder le fuseau sur tous les dialectes ; pas de table
  `Locks` — verrou distribué = implémentation de `LockObject` à brancher).
- `storage_sql/storage.py` : `SqlWorkflowStorage(engine|url)` —
  `create_schema()`, `load_by_external_id` (se branche tel quel sur le
  callback du processor), `get`/`get_all`, `save_workflow` en **upsert
  idempotent** de l'agrégat complet (le rejeu ne duplique rien). Bug du
  source non reproduit : `WorkflowStoreSql.Save` passait `txtStep` dans
  `DatasWorkflow`.
- `storage_sql/outputs.py` : `SqlUnitOfWork` (une connexion + une
  transaction partagées par toute la chaîne — rollback SQL réel testé),
  `SqlPushModelOutputAction`, fabrique `sql_output(storage, bus=None)` =
  SetProperties → (bus ?) → SqlPushModel. Les actions matérialisées sont
  persistées avec l'agrégat (= outbox) ; pas de table bus séparée.
- `outputs/base.py` : `OutputBus` (ABC, contrat Outputs.Mom) +
  `BusOutputAction(bus, kinds)` générique.
- SQLite `create_engine("sqlite://")` en tests (pool mémoire persistant) ;
  `pytest.importorskip("sqlalchemy")` ; extra `sql` + dev dans pyproject.

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
