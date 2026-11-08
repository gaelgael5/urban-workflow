# urban-workflow

*Français · [English](README.en.md)*

Moteur de workflow piloté par un **langage dédié** (DSL) — portage Python de
[Black-Beard-Sdk/Workflow](https://github.com/Black-Beard-Sdk/Workflow)
(.NET), dont le système de normalisation des sorties JSON est remplacé par
[urban-json](https://pypi.org/project/urban-json/) (moteur JSLT) : les
messages produits par le moteur sont décrits par des templates `.jslt`
déclaratifs, modifiables sans redéploiement.

## Un workflow en quelques lignes

```sql
NAME ValidationAchat VERSION 1
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise 'une demande est déposée';
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil';
DEFINE ACTION NotifierValideur (TEXT dossier)  'demande d''approbation';
DEFINE CONST  seuil_auto 500 'approbation automatique sous ce montant';

INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage'
    ON EVENT DemandeSoumise
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        EXECUTE NotifierValideur(dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;
DEFINE STATE Approuvee    'approbation automatique' ;
DEFINE STATE EnValidation 'en attente d''un valideur'
    EXPIRE AFTER 3 DAY SWITCH Expiree
;
DEFINE STATE Expiree      'sans réponse' ;
```

```python
from urban_workflow import (
    FunctionRegistry, MemoryStorage, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output

rules = FunctionRegistry("rule")
rules.add("MontantInferieur", lambda ctx, seuil: float(
    ctx.incoming_event.extended_datas.get("Montant", 0)) < seuil)

storage = MemoryStorage()
configs = WorkflowsConfig().add_document(parse_config(SCRIPT, rules=rules))
processor = WorkflowProcessor(configs, WorkflowFactory())
processor.load_existing_workflows_by_external_id = (
    lambda key: storage.get_by(Workflow, key, "external_id"))
processor.output_actions = default_memory_output(storage)
engine = WorkflowEngine(processor)

engine.evaluate_event({"Name": "DemandeSoumise", "ExternalId": "DA-42",
                       "Type": "achat", "Montant": 120})
```

## Documentation

| Guide | Contenu |
|---|---|
| [docs/guide-dsl.md](docs/guide-dsl.md) | **Créer un workflow** : référence complète du langage — création d'instances, transitions `SWITCH`, conditions `WHEN`, actions, expiration, fragments |
| [docs/guide-regles.md](docs/guide-regles.md) | **Règles et scripts** : `DEFINE RULE … AS @script`, `ScriptRegistry` multi-langage, langage `expression` (opérateurs, fonctions, sémantique `NULL`), contrôles |
| [docs/guide-artefacts.md](docs/guide-artefacts.md) | **Artefacts JSON** : `DEFINE ARTIFACT … AS @schema USING @script`, scripts `jslt` (urban-json), `@artifact.Nom` dans les actions, validation par schéma |
| [docs/guide-integration.md](docs/guide-integration.md) | **L'utiliser dans du code** : règles métier, assemblage du moteur, templates JSLT, chaîne de sorties, événements techniques |
| [docs/guide-tests.md](docs/guide-tests.md) | **Le tester** : règles pures, configuration, templates, scénarios de bout en bout |
| [docs/analyse-portage.md](docs/analyse-portage.md) | Analyse du projet source et choix structurants du portage |

English versions: [docs/en/dsl-guide.md](docs/en/dsl-guide.md) ·
[docs/en/rules-guide.md](docs/en/rules-guide.md) ·
[docs/en/artifacts-guide.md](docs/en/artifacts-guide.md) ·
[docs/en/integration-guide.md](docs/en/integration-guide.md) ·
[docs/en/testing-guide.md](docs/en/testing-guide.md)

## Playground

Des **composants web indépendants** (éditeur avec intellisense,
diagramme, schémas, scripts, simulation sur le vrai moteur…) qu'une
application monte selon ses besoins, et une page qui les assemble —
distribution séparée [`urban-workflow-playground`](playground/README.md) :

```bash
pip install urban-workflow-playground
urban-workflow-playground     # http://127.0.0.1:8777
```

## Installation et développement

```bash
pip install -e .[dev]
python3 -m pytest -q
```

Dépendance unique du cœur : `urban-json` (qui apporte le runtime ANTLR du
parseur DSL). Python ≥ 3.10.

## État du portage

Socle, DSL (grammaires ANTLR reprises du source), moteur, templating
urban-json et persistance SQL (extra `[sql]`, SQLAlchemy Core) sont
fonctionnels et testés (scénarios de bout en bout *script DSL →
événements → états → messages*, cycle de vie persisté en SQL), avec CI
GitHub Actions (tests Python 3.10 → 3.13, lint ruff). Les bugs connus du
moteur source ne sont pas reproduits — chacun est couvert par un test
dédié.

## Licence

Voir [LICENSE](LICENSE).
