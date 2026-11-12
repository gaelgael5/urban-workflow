# urban-workflow

*English · [Français](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/README.md)*

Workflow engine driven by a **domain-specific language** (DSL) — a Python
port of [Black-Beard-Sdk/Workflow](https://github.com/Black-Beard-Sdk/Workflow)
(.NET), whose JSON output normalization system is replaced by
[urban-json](https://pypi.org/project/urban-json/) (a JSLT engine): the
messages produced by the engine are described by declarative `.jslt`
templates that can be changed without redeploying.

## A workflow in a few lines

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

| Guide | Contents |
|---|---|
| [docs/en/dsl-guide.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/en/dsl-guide.md) | **Writing a workflow**: complete language reference — instance creation, `SWITCH` transitions, `WHEN` conditions, actions, expiration, event schemas, **deduplication keys** (`UNIQUE`, `DedupKey`, automatic fallback), fragments |
| [docs/en/rules-guide.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/en/rules-guide.md) | **Rules and scripts**: `DEFINE RULE … AS @script`, multi-language `ScriptRegistry`, the `expression` language (operators, functions, `NULL` semantics), checks |
| [docs/en/artifacts-guide.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/en/artifacts-guide.md) | **JSON artifacts**: `DEFINE ARTIFACT … AS @schema USING @script`, `jslt` scripts (urban-json), `@artifact.Name` in actions, schema validation |
| [docs/en/integration-guide.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/en/integration-guide.md) | **Using it in code**: business rules, engine assembly, JSLT templates, output chain, technical events |
| [docs/en/testing-guide.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/en/testing-guide.md) | **Testing it**: pure rules, configuration, templates, end-to-end scenarios |
| [docs/analyse-portage.md](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/docs/analyse-portage.md) (French) | Analysis of the source project and the key design choices of the port |

## Playground

**Standalone web components** (editor with intellisense, diagram,
schemas, scripts, simulation on the real engine…) that an application
mounts as needed, and a page that assembles them — a separate
distribution, [`urban-workflow-playground`](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/playground/README.en.md):

```bash
pip install urban-workflow-playground
urban-workflow-playground     # http://127.0.0.1:8777
```

## Installation and development

```bash
pip install -e .[dev]
python3 -m pytest -q
```

Single core dependency: `urban-json` (which brings the ANTLR runtime used
by the DSL parser). Python ≥ 3.10.

## Porting status

Foundation, DSL (ANTLR grammars taken from the source), engine, urban-json
templating and SQL persistence (`[sql]` extra, SQLAlchemy Core) are
functional and tested (end-to-end scenarios *DSL script → events → states
→ messages*, lifecycle persisted in SQL), with GitHub Actions CI (Python
3.10 → 3.13 tests, ruff lint). Known bugs of the source engine are not
reproduced — each one is covered by a dedicated test.

## License

See [LICENSE](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/LICENSE).
