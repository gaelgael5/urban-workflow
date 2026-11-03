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
- **named and typed**: the Python signature is the contract — `WHEN`
  calls in the script are validated against it at load time.

```python
# rules.py
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("AmountBelow")
def amount_below(ctx: RunContext, threshold: float) -> bool:
    amount = ctx.incoming_event.extended_datas.get("Amount")
    return amount is not None and float(amount) < threshold
```

### Testing a rule alone

A `RunContext` is built by hand — three dataclasses, no engine:

```python
from urban_workflow import IncomingEvent, RunContext, Workflow

def make_ctx(**payload) -> RunContext:
    return RunContext(
        workflow=Workflow(workflow_name="PurchaseValidation", external_id="PR-1"),
        incoming_event=IncomingEvent(name="RequestSubmitted",
                                     extended_datas=dict(payload)),
    )

def test_amount_below():
    assert amount_below(make_ctx(Amount=120), threshold=500.0) is True
    assert amount_below(make_ctx(Amount=900), threshold=500.0) is False
    assert amount_below(make_ctx(), threshold=500.0) is False   # missing data
```

For a rule that inspects history (`ctx.workflow.events`), append
`Event(name=…, to_state=…)` items to `workflow.events`.

## 2. Testing a DSL script (the configuration)

`parse_config` turns the script into a `WorkflowConfig`: verify the
**structure** (states, transitions, resolved targets) and the **behaviour
of the compiled conditions**, without running the engine.

```python
from urban_workflow.dsl import parse_config
from rules import rules

def test_flow_structure():
    config = parse_config(SCRIPT, rules=rules, filename="validation.wf")

    assert set(config.states) == {
        "Dispatch", "Incomplete", "UnderReview", "Approved", "Rejected", "Expired",
    }
    transition = config.states["UnderReview"].events["ApprovalGranted"].transitions[0]
    assert transition.target_state is config.states["Approved"]

def test_dispatch_condition():
    config = parse_config(SCRIPT, rules=rules)
    branches = config.states["Dispatch"].events["RequestSubmitted"].transitions

    # WHEN closures evaluate directly against a hand-built context.
    assert branches[0].when_rule(make_ctx()) is True            # incomplete
    assert branches[1].when_rule(make_ctx(Amount=120)) is True  # below threshold
    assert branches[2].when_rule is None                        # default branch
```

### Testing that bad scripts are rejected

Load errors are positioned — tests can demand it:

```python
import pytest
from urban_workflow.exceptions import (
    DslSyntaxError, InvalidMethodReferenceError, MissingStateError,
)

def test_undeclared_action():
    script = SCRIPT.replace("NotifyApprover(", "Unknown(")
    with pytest.raises(InvalidMethodReferenceError, match=r"validation\.wf:\d+:\d+"):
        parse_config(script, rules=rules, filename="validation.wf")

def test_positioned_syntax_error():
    with pytest.raises(DslSyntaxError) as excinfo:
        parse_config("NAME x DEFINE EVENT e 'e'", rules=rules)  # missing ;
    assert excinfo.value.errors[0].line >= 1
```

### Functional log

Every rule evaluation traces a line in `ctx.functional_log`
(`AmountBelow(threshold=500.0) -> True`): handy in assertions to verify
*why* a branch was taken.

## 3. Testing output templates

A template is tested as a triplet *context document → template → result*,
without the engine:

```python
from urban_workflow.templating import TemplateRegistry, build_action_document

def test_notify_approver_template():
    registry = TemplateRegistry().add_directory("templates/")

    ctx = make_ctx(Amount=900)
    action = notify_action_config.map(ctx)       # ResultActionConfig.map
    body = registry.transform("NotifyApprover",
                              build_action_document(ctx, action))

    assert body == {
        "Order": "notify",
        "Case": "PR-1",
        "Amount": 900,
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
def engine_and_storage():
    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(parse_config(SCRIPT, rules=rules))
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = (
        lambda key: storage.get_by(Workflow, key, "external_id")
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage

def event(name, case, **data):
    return {"Name": name, "Uuid": str(uuid4()), "ExternalId": case,
            "Type": "purchase", **data}

def test_auto_approval(engine_and_storage):
    engine, storage = engine_and_storage
    engine.evaluate_event(event("RequestSubmitted", "PR-1", Amount=120))

    case = storage.get_by(Workflow, "PR-1", "external_id")[0]
    assert case.current_state == "Approved"
    assert case.extended_datas["Status"] == "approved"      # STORE
```

### Testing an expiry

Expiry is simulated by replaying the reminder yourself, as the deferred
bus would:

```python
def test_expiry(engine_and_storage):
    engine, storage = engine_and_storage
    engine.evaluate_event(event("RequestSubmitted", "PR-3", Amount=900))
    case = storage.get_by(Workflow, "PR-3", "external_id")[0]
    assert case.current_state == "UnderReview"

    # The deferred reminder was pushed on entering the state.
    reminder = storage.get_all(PushedAction)[-1]
    assert reminder.execute_message["Body"]["Delay"] == 3 * 24 * 60

    # When due, the bus would send the __expired event back:
    engine.evaluate_event(event(
        "__expired", "PR-3",
        WorkflowId=str(case.uuid), CurrentState="UnderReview",
    ))
    case = storage.get_by(Workflow, "PR-3", "external_id")[0]
    assert case.current_state == "Expired"
```

A stale reminder (the state changed meanwhile) must be a no-op — a
`CurrentState` different from the actual state leaves the workflow alone.

## 5. Controlling time

The whole engine dates its objects through `WorkflowClock.now()`. For
deterministic tests:

```python
from datetime import datetime, timezone
from urban_workflow import WorkflowClock

NOW = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)

def test_frozen_output_date(engine_and_storage):
    engine, storage = engine_and_storage
    with WorkflowClock.frozen(NOW):
        engine.evaluate_event(event("RequestSubmitted", "PR-4", Amount=120))
    action = storage.get_all(PushedAction)[0]
    assert action.execute_message["Body"]["PushedAt"] == NOW.isoformat()
```

`WorkflowClock.set_provider(...)` / `reset()` exist for finer control (a
step-by-step clock).

## 6. Pitfalls and idioms

- **A fresh event `Uuid` per send**: the engine ignores an
  already-integrated uuid (replay protection). A test reusing the same
  uuid "does nothing" the second time — by design.
- **`MATCHING` applies at creation**: a test event without the filter's
  pairs creates no instance — include them in the test's event factory.
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
  `tests/test_docs_examples.py` (the guides' worked example).
