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
- [ ] **Étape 2 — DSL** (prochaine, le gros morceau) : grammaires ANTLR
  reprises + visiteur → `WorkflowConfig`
- [ ] Étape 3 — Moteur (processor, engine, locks)
- [ ] Étape 4 — Templating urban-json (TranslateActions)
- [ ] Étape 5 — Persistance SQL (SQLAlchemy, extra optionnel)
- [ ] Étape 6 — Finitions (docs, CI)

## Étape 2 (DSL) — notes de reprise

1. Le dépôt source doit être recloné (conteneur éphémère) :
   `git clone --depth 1 https://github.com/Black-Beard-Sdk/workflow /home/user/black-beard-sdk/workflow`
2. Grammaires à reprendre **telles quelles** :
   `Src/Black.beard.Workflow.AntlrParser/Parser/Grammar/WorkflowLexer.g4` et
   `WorkflowParser.g4` → les copier dans `urban_workflow/dsl/grammar/`.
3. Générer le parseur : cible **Python3**, ANTLR 4.13.2 (même runtime
   qu'urban-json, déjà en dépendance transitive). Commiter le code généré +
   script de régénération.
4. Réécrire `WorkflowConfigVisitor` (1 292 lignes C#, même chemin source) en
   Python sur la base `WorkflowParserBaseVisitor` générée. Il construit un
   `urban_workflow.WorkflowConfig` :
   - déclarations `DEFINE EVENT/RULE/ACTION/CONST` + validation stricte
     (règle/action non déclarée, arguments vs signature, doublons) —
     s'appuyer sur `FunctionRegistry.validate_call` ;
   - conditions `WHEN` : arbre NOT/AND/OR de `rule(args)` → **composition de
     closures** (pas d'arbres d'expressions) ;
   - chemins `@Event.X` → `urban_workflow.values.ContextRef` (déjà compatible
     CamelCase du DSL → attributs snake_case) ;
   - erreurs positionnées (fichier, ligne, colonne) → `RuleSpan` ;
   - `INCLUDE` / `FRAGMENT` (fragments réutilisables).
5. Tests golden : l'exemple complet du README source + les cas de
   `Src/UnitTestWorkflow/ParserUnitTest.cs` doivent produire une config
   équivalente.

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
