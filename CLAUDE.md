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
- [ ] **Étape 3 — Moteur** (prochaine) : processor, engine, locks
- [ ] Étape 4 — Templating urban-json (TranslateActions)
- [ ] Étape 5 — Persistance SQL (SQLAlchemy, extra optionnel)
- [ ] Étape 6 — Finitions (docs, CI)

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

## Étape 3 (Moteur) — notes de reprise

1. Recloner le source si absent :
   `git clone --depth 1 https://github.com/Black-Beard-Sdk/workflow /home/user/black-beard-sdk/workflow`
2. À porter (dans `Src/Black.Beard.Workflows.Models/Workflows/`) :
   `WorkflowEngine` (locks par clé `zlib.crc32(external_id)`),
   `WorkflowProcessor` (création via Initializers + CONCURENCY, transitions,
   règles d'entrée/sortie, mode récursif, collecte des `ResultAction`),
   `RunContext.Set`, `WorkflowFactory`, chaîne `AppendEvents/`,
   sorties mémoire (`Outputs/Memories/` : MemoryStorage, décorateurs
   SetProperties/PushBus/PushModel + transaction).
3. Bugs §5 de l'analyse à ne pas reproduire : `UseResource.Decrement`,
   `CreateBaseIncomingEvent` (conditions inversées).
4. Spécification de référence : `Src/UnitTestWorkflow/WorkflowsUnitTest.cs`,
   `IncomingEventUnitTest.cs`, `WorkflowsConfigUnitTest1.cs` + les scénarios
   bout-en-bout de `ParserUnitTest.cs` (TestFilter, TestInitialize,
   TestInitializeWithJumpState, TestExpire) — à porter en pytest sur les
   scripts DSL de `tests/test_dsl.py`.

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
