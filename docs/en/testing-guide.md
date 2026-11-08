# Testing guide — writing testable rules and testing workflows

A workflow is tested at four levels, from fastest to most integrated:
the **business rules** alone, the **configuration** produced by a DSL
script, the output **templates**, and the **end-to-end scenario**
(events → states → messages). This guide gives the recipe for each, with
pytest. Version française : [../guide-tests.md](../guide-tests.md).

## 1. Writing rules made to be tested

A rule is a callable `(ctx, **kwargs) -> bool`. For it to be testable in
isolation:

- **pure**: it reads the context and returns a boolean — no I/O, no
  direct clock (go through `WorkflowClock.now()` when a date is needed),
  no context mutation;
- **defensive**: data missing from the payload is a normal case (return
  `False`), not an exception;
- **named and typed**: the Python signature is the contract — the parser
  validates the script's `WHEN` calls against it.

```python
# regles.py
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("MontantInferieur")
def montant_inferieur(ctx: RunContext, seuil: float) -> bool:
    montant = ctx.incoming_event.extended_datas.get("Montant")
    return montant is not None and float(montant) < seuil
```

### Testing a rule alone

A `RunContext` is built by hand — three dataclasses, no engine:

```python
from urban_workflow import IncomingEvent, RunContext, Workflow

def make_ctx(**payload) -> RunContext:
    return RunContext(
        workflow=Workflow(workflow_name="ValidationAchat", external_id="DA-1"),
        incoming_event=IncomingEvent(name="DemandeSoumise",
                                     extended_datas=dict(payload)),
    )

def test_montant_inferieur():
    assert montant_inferieur(make_ctx(Montant=120), seuil=500.0) is True
    assert montant_inferieur(make_ctx(Montant=900), seuil=500.0) is False
    assert montant_inferieur(make_ctx(), seuil=500.0) is False   # missing data
```

For a rule that inspects history (`ctx.workflow.events`), append
`Event(name=…, to_state=…)` items to `workflow.events`.

## 2. Testing a DSL script (the configuration)

`parse_config` turns the script into a `WorkflowConfig`: verify the
**structure** (states, transitions, resolved targets) and the **behaviour
of the compiled conditions**, without running the engine.

```python
from urban_workflow.dsl import parse_config
from regles import rules

def test_structure_du_circuit():
    config = parse_config(SCRIPT, rules=rules, filename="validation.wf")

    assert set(config.states) == {
        "Tri", "Incomplete", "EnValidation", "Approuvee", "Rejetee", "Expiree",
    }
    transition = config.states["EnValidation"].events["ValidationAccordee"].transitions[0]
    assert transition.target_state is config.states["Approuvee"]

def test_condition_du_tri():
    config = parse_config(SCRIPT, rules=rules)
    branches = config.states["Tri"].events["DemandeSoumise"].transitions

    # WHEN closures evaluate directly against a hand-built context.
    assert branches[0].when_rule(make_ctx()) is True            # incomplete
    assert branches[1].when_rule(make_ctx(Montant=120)) is True # below threshold
    assert branches[2].when_rule is None                        # default branch
```

### Testing that bad scripts are rejected

Load errors are positioned — tests can demand it:

```python
import pytest
from urban_workflow.exceptions import (
    DslSyntaxError, InvalidMethodReferenceError, MissingStateError,
)

def test_action_non_declaree():
    script = SCRIPT.replace("NotifierValideur(", "Inconnue(")
    with pytest.raises(InvalidMethodReferenceError, match=r"validation\.wf:\d+:\d+"):
        parse_config(script, rules=rules, filename="validation.wf")

def test_erreur_de_syntaxe_positionnee():
    with pytest.raises(DslSyntaxError) as excinfo:
        parse_config("NAME x DEFINE EVENT e 'e'", rules=rules)  # missing ;
    assert excinfo.value.errors[0].line >= 1
```

### Functional log

Every rule evaluation traces a line in `ctx.functional_log`
(`MontantInferieur(seuil=500.0) -> True`): handy in assertions to verify
*why* a branch was taken.

## 3. Testing output templates

A template is tested as a triplet *context document → template → result*,
without the engine:

```python
from urban_workflow.templating import TemplateRegistry, build_action_document

def test_template_notifier_valideur():
    registry = TemplateRegistry().add_directory("templates/")

    ctx = make_ctx(Montant=900)
    action = config_action_notifier.map(ctx)     # ResultActionConfig.map
    body = registry.transform("NotifierValideur",
                              build_action_document(ctx, action))

    assert body == {
        "Ordre": "notifier",
        "Dossier": "DA-1",
        "Montant": 900,
    }
```

For reproducible dated outputs, freeze the clock (see §5).

## 4. Testing an end-to-end scenario

The trio `MemoryStorage` + `default_memory_output` + `WorkflowEngine`
gives a complete in-memory engine, no infrastructure:

```python
from uuid import uuid4

from urban_workflow import (
    MemoryStorage, PushedAction, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output
import pytest

@pytest.fixture
def moteur():
    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(parse_config(SCRIPT, rules=rules))
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = (
        lambda key: storage.get_by(Workflow, key, "external_id")
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage

def evenement(nom, dossier, **donnees):
    return {"Name": nom, "Uuid": str(uuid4()), "ExternalId": dossier,
            "Type": "achat", **donnees}

def test_approbation_automatique(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-1", Montant=120))

    dossier = storage.get_by(Workflow, "DA-1", "external_id")[0]
    assert dossier.current_state == "Approuvee"
    assert dossier.extended_datas["Statut"] == "approuvee"      # STORE

def test_refus(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-2", Montant=900))
    engine.evaluate_event(evenement("ValidationRefusee", "DA-2",
                                    Motif="budget épuisé"))

    dossier = storage.get_by(Workflow, "DA-2", "external_id")[0]
    assert dossier.current_state == "Rejetee"
    # The message pushed on refusal carries the incoming event's reason.
    notification = next(a for a in dossier.last_event.actions
                        if a.name == "NotifierDemandeur")
    assert notification.execute_message["Body"]["Arguments"]["motif"] == "budget épuisé"
```

### Testing an expiry

Expiry is simulated by replaying the reminder yourself, as the deferred
bus would:

```python
def test_expiration(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-3", Montant=900))
    dossier = storage.get_by(Workflow, "DA-3", "external_id")[0]
    assert dossier.current_state == "EnValidation"

    # The deferred reminder was pushed on the bus on entering the state.
    rappel = storage.get_all(PushedAction)[-1]
    assert rappel.execute_message["Body"]["Delay"] == 3 * 24 * 60

    # When due, the bus would send the __expired event back:
    engine.evaluate_event(evenement(
        "__expired", "DA-3",
        WorkflowId=str(dossier.uuid), CurrentState="EnValidation",
    ))
    dossier = storage.get_by(Workflow, "DA-3", "external_id")[0]
    assert dossier.current_state == "Expiree"
```

And a stale reminder (the state changed meanwhile) must be a no-op — a
`CurrentState` different from the actual state leaves the workflow alone.

## 5. Controlling time

The whole engine dates its objects through `WorkflowClock.now()`. For
deterministic tests:

```python
from datetime import datetime, timezone
from urban_workflow import WorkflowClock

NOW = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)

def test_date_de_sortie_figee(moteur):
    engine, storage = moteur
    with WorkflowClock.frozen(NOW):
        engine.evaluate_event(evenement("DemandeSoumise", "DA-4", Montant=120))
    action = storage.get_all(PushedAction)[0]
    assert action.execute_message["Body"]["PushedAt"] == NOW.isoformat()
```

`WorkflowClock.set_provider(...)` / `reset()` exist for finer control (a
clock that advances step by step).

## 6. Pitfalls and idioms

- **A fresh event `Uuid` per send**: the engine ignores an
  already-integrated uuid (replay protection). A test reusing the same
  uuid "does nothing" the second time — by design.
- **`MATCHING` applies at creation**: a test event without the filter's
  pairs creates no instance — remember to include them in the test's
  event factory.
- **Test the kind, not the implementation**: `EXECUTE` → `$_push`,
  `STORE` → `$_update`, custom kind → as-is. The output chain is tested by
  checking `storage.get_all(PushedAction)` and the workflow's
  `extended_datas`.
- **Transactions**: to test a custom output link, make `_execute_impl`
  fail and verify the rollback happened and the exception propagated (the
  engine rolls back the whole chain).
- **Reference suite**: the repository tests are themselves full examples —
  `tests/test_dsl.py` (language goldens), `tests/test_engine.py` (engine),
  `tests/test_engine_dsl.py` (DSL end-to-end), `tests/test_templating.py`
  (templates), `tests/test_storage_sql.py` (SQL persistence),
  `tests/test_docs_examples.py` (guide examples, executed as written).
