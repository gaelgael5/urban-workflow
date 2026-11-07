# Integration guide — using a workflow from code

How to load DSL scripts, implement business rules, assemble the engine,
process events and collect outputs. The language itself is described in
[dsl-guide.md](dsl-guide.md), testing in
[testing-guide.md](testing-guide.md). Version française :
[../guide-integration.md](../guide-integration.md).

## 1. Quick start

```python
from urban_workflow import (
    FunctionRegistry, MemoryStorage, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output

# 1. Business rules: callables (ctx, **kwargs) -> bool
rules = FunctionRegistry("rule")
rules.add("IsComplete", lambda ctx, fields: all(
    ctx.incoming_event.extended_datas.get(f) is not None
    for f in fields.split(",")
))
rules.add("AmountBelow", lambda ctx, threshold: float(
    ctx.incoming_event.extended_datas.get("Amount", 0)
) < threshold)

# 2. Load and validate the DSL script
script = open("workflows/validation.wf", encoding="utf-8").read()
config = parse_config(script, rules=rules, filename="validation.wf")

# 3. Assemble the engine
storage = MemoryStorage()
configs = WorkflowsConfig().add_document(config)

processor = WorkflowProcessor(configs, WorkflowFactory())
processor.load_existing_workflows_by_external_id = (
    lambda key: storage.get_by(Workflow, key, "external_id")
)
processor.output_actions = default_memory_output(storage)

engine = WorkflowEngine(processor)

# 4. Process an event
engine.evaluate_event({
    "Name": "RequestSubmitted",
    "Uuid": "4f6c6c6f-0000-4000-8000-000000000001",
    "ExternalId": "PR-2026-0042",     # the subject identifier
    "EventDate": "2026-11-03T10:00:00+00:00",
    "Type": "purchase",               # consumed by MATCHING
    "Amount": 120,                    # business data
})

case = storage.get_by(Workflow, "PR-2026-0042", "external_id")[0]
print(case.current_state)
```

## 2. Business rules

A rule is a callable `(ctx, **kwargs) -> bool`. The first parameter is
always the `RunContext`; the rest are the DSL call's named arguments,
already resolved (literals converted to the declared type, `@` paths read
from the context, constants substituted).

```python
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("AmountBelow")
def amount_below(ctx: RunContext, threshold: float) -> bool:
    amount = ctx.incoming_event.extended_datas.get("Amount")
    return amount is not None and float(amount) < threshold
```

What the context exposes:

| Attribute | Content |
|---|---|
| `ctx.incoming_event` | The incoming event (`name`, `external_id`, `event_date`, `extended_datas` = the payload) |
| `ctx.workflow` | The instance (`current_state`, `events` = history, `extended_datas` = business state written by `STORE`) |
| `ctx.event` | The event being integrated (`from_state`, `to_state`) |
| `ctx.functional_log` | Rule-evaluation journal (audit) |

Call validation (`WHEN AmountBelow(threshold = …)`) runs against the
**callable's signature** at script load time: an unknown or missing
argument is a load error, not a run-time one.

Best practices (detailed in [testing-guide.md](testing-guide.md)):
**pure** rules (no I/O) that read the context and return a boolean; every
side effect goes through actions.

### Rules referencing a script (`AS @script`)

A rule declared `DEFINE RULE R (…) '…' AS @name;` is not looked up in the
`FunctionRegistry`: its method is the script `name` of the
`ScriptRegistry`, loaded at engine start like schemas.

```python
from urban_workflow.scripts import ScriptRegistry

scripts = (
    ScriptRegistry()
    .add_directory("scripts/")                  # one file per script (.expr…)
    .add_script("amount_below", "@IncomingEvent.Amount < threshold")
    .add_function("solvent", lambda ctx, customer: check(customer))  # Python
)
config = parse_config(script, rules=rules, scripts=scripts)
```

A file's language comes from its extension (`.expr` = `expression`
language); `add_function` registers a `(ctx, **params)` callable whose
signature is checked against the declaration. Another language is added
with `register_language` (a `ScriptLanguage` subclass: `name`,
`extensions`, `check`, `compile`). Details: [rules-guide.md](rules-guide.md).

## 3. Loading scripts

### A single script

```python
from urban_workflow.dsl import parse_config

config = parse_config(script_text, rules=rules, filename="validation.wf")
```

`parse_config` raises the positioned errors of
[dsl-guide.md](dsl-guide.md) §10. `filename` only feeds the messages.

### A directory with fragments

```python
from urban_workflow import WorkflowsConfig
from urban_workflow.dsl import WorkflowConfigVisitor, load_directory

def visitor_factory():
    return WorkflowConfigVisitor(rules=rules)

configs = load_directory(WorkflowsConfig(), visitor_factory, "workflows/", "*.wf")
```

`FRAGMENT` files are visited before the scripts that `INCLUDE` them; each
full script becomes a document of `configs`.

### Fine-grained control

```python
from urban_workflow.dsl import WorkflowScriptParser, WorkflowConfigVisitor

parser = WorkflowScriptParser.parse_string(script_text, filename="x.wf")
parser.check()                 # raises DslSyntaxError on syntax errors
parser.includes                # declared INCLUDE files
parser.is_fragment             # FRAGMENT script?
config = parser.visit(WorkflowConfigVisitor(rules=rules))
```

## 4. Outputs: actions, templates, headers

When a branch triggers `EXECUTE Action(…)`, the engine collects the action
then **materialises** it into a message via an `ActionTranslator`. Two
implementations:

- `DefaultActionTranslator` (default): generic JSON body, zero
  configuration;
- `JsltActionTranslator`: body produced by an **urban-json JSLT template**
  per action name — the recommended path.

```python
from urban_workflow.templating import (
    JsltActionTranslator, MetadataRegistry, TemplateRegistry,
)

templates = TemplateRegistry().add_directory("templates/")   # *.jslt
metadatas = MetadataRegistry(default={"channel": "purchasing-bus"})
metadatas.add_metadata("NotifyApprover", {"channel": "mail", "ttl": "3600"})

processor = WorkflowProcessor(
    configs, WorkflowFactory(),
    translator=JsltActionTranslator(templates, metadatas),
)
```

### `.jslt` templates

One file per action name (`NotifyApprover.jslt`), `default.jslt` as the
fallback. A template navigates the action's **context document**:

```jslt
{
    "Order":    "notify",
    "Level":    $.action.arguments.level,
    "Case":     $.workflow.external_id,
    "State":    $.workflow.state,
    "Amount":   $.incoming.Amount,
    "IssuedAt": $.now
}
```

Available sections: `$.action` (uuid, name, kind, delay, resolved
arguments), `$.workflow` (uuid, name, version, external_id, state +
extended data), `$.event` (uuid, name, from_state, to_state + data),
`$.incoming` (uuid, name, external_id, dates + payload), `$.now`.

Without a dedicated template or `default.jslt`, the built-in default
template produces the source engine's historical shape: `Uuid`, `Name`,
`PushedAt`, `Arguments`, `WorkflowId`, `EventId`, `From_State`,
`To_State`.

Custom urban-json functions can be exposed to templates:

```python
from urban_json import default_registry

functions = default_registry.copy()
functions.register("upper", lambda ctx, v: str(v).upper())
templates = TemplateRegistry(functions=functions)
```

### The produced message

Each materialised action is a `PushedAction` attached to the history
event, with `execute_message = {"Header": …, "Body": …}`: `Header` comes
from the `MetadataRegistry` (routing headers), `Body` from the template. A
deferred action (`WAITING`, expiry reminder) has a wrapped body:
`{"Name": "$_reminder", "Delay": minutes, "Message": body}`.

## 5. The output chain and persistence

On each evaluation, the processor builds an **output chain** (decorator
pattern) and runs it under a transaction:

```python
processor.output_actions = default_memory_output(storage)
# equivalent to:
#   SetPropertiesOutputAction(        # applies STORE to the workflow
#       PushBusOutputAction(storage,  # pushes $_push actions to the "bus"
#           PushModelOutputAction(storage)))  # persists the workflow
```

The core does **no I/O**: wiring real infrastructure means providing two
extension points —

1. `processor.load_existing_workflows_by_external_id`: load a subject's
   instances from your storage;
2. `processor.output_actions`: a chain factory whose links derive from
   `OutputAction` (and `Transaction` for real commit/rollback).

If a link fails, the whole chain's transaction is rolled back and the
exception propagates — the event can be replayed without duplicates.

### Ready-made SQL persistence (`[sql]` extra)

For durable deployment without writing your own links, the `sql` extra
(`pip install urban-workflow[sql]`) ships a SQLAlchemy Core storage —
SQLite in development, PostgreSQL or other in production:

```python
from sqlalchemy import create_engine
from urban_workflow.storage_sql import SqlWorkflowStorage, sql_output

storage = SqlWorkflowStorage(create_engine("sqlite:///workflows.db"))
storage.create_schema()    # workflows / workflow_events / workflow_actions tables

processor.load_existing_workflows_by_external_id = storage.load_by_external_id
processor.output_actions = sql_output(storage)
```

The three tables follow the source engine's logical schema; each workflow
is persisted as an aggregate (instance, event history, materialised
actions with their JSON messages — the outbox). Writes are idempotent
(replaying a save duplicates nothing) and the whole chain shares **one SQL
transaction**: if a link fails, nothing is written.

To also push to a broker, plug an `OutputBus` implementation:

```python
from urban_workflow.outputs import OutputBus

class RabbitBus(OutputBus):
    def push(self, action):
        channel.publish(json.dumps(action.execute_message))

processor.output_actions = sql_output(storage, bus=RabbitBus())
```

Locking caveat: `MemoryLocker` only protects one process. Several engine
instances on the same database require a distributed `LockObject`
(database lock, Redis…).

## 6. Events on the engine side

### Payload format

`engine.evaluate_event(...)` accepts JSON (string), a dict, or an
already-built `IncomingEvent`. Recognised properties (CamelCase, inherited
from the source format):

| Key | Role |
|---|---|
| `Name` | Event name (required for routing) |
| `Uuid` | Event identity — **the replay-without-duplicates key** |
| `ExternalId` | Subject identifier: groups instances |
| `CreationDate`, `EventDate` | ISO 8601 dates |
| `IntegrationDate` | **Set by the engine** (`WorkflowClock`) when `evaluate_event` receives the event: the date it entered the system. A value sent by the emitter is ignored. Kept in the history (`Event.integration_date`, SQL column `integration_date`) and exposed to templates (`event.integration_date`, `incoming.integration_date`) |
| *everything else* | Business data (`extended_datas`), visible to rules, `MATCHING` filters and templates |

An invalid payload raises `InvalidIncomingEventFormatError`.

### Locking

The engine serialises processing per subject: the key (`ExternalId` by
default, customisable via `thread_safe_key`) is locked during evaluation
(`MemoryLocker` in memory; implement `LockObject` for a distributed lock).
A lock not acquired in time raises `LockFailedError`.

### Technical events

| Event | Emitted by | Effect |
|---|---|---|
| `__expired` | Your reminder bus, when an `EXPIRE AFTER` falls due (with `WorkflowId` and `CurrentState`) | Applies the expiry transition if the state has not changed |
| `__cancelReminderAction` | The engine, when leaving an expirable state | For your bus to interpret: cancel the pending reminder |
| `$_result` | Your infrastructure, reporting the result of a pushed action (with `EventId` and `TaskId`) | Attaches the result to the originating `PushedAction`, no history entry |
| `$_reminder` | — (the envelope of deferred pushed actions) | Your bus replays it after `Delay` minutes |

The reminder-bus contract: receive `$_reminder` messages and, when due,
send their inner `Message` back as an incoming event.

## 7. Several workflows, several versions

```python
configs = (
    WorkflowsConfig()
    .add_document(parse_config(purchases_v1, rules=rules))
    .add_document(parse_config(purchases_v2, rules=rules))
    .add_document(parse_config(leave_requests, rules=rules))
)

# New "Purchases" instances are only created on v2;
# existing v1 instances keep running on their own configuration.
configs.set_version_selector("Purchases", 2)
```

Event routing: `MATCHING` filters select the workflows candidate for
**creation**; **existing** instances are found by `ExternalId` and handled
with their original version's configuration. One event can therefore
impact several workflows at once.

## 8. Import summary

```python
from urban_workflow import (            # core, no heavy dependency
    FunctionRegistry, RunContext, Workflow, IncomingEvent,
    WorkflowsConfig, WorkflowFactory, WorkflowProcessor, WorkflowEngine,
    MemoryStorage, MemoryLocker, OutputAction, Transaction,
    WorkflowClock, constants,
)
from urban_workflow.dsl import (        # ANTLR parser (the DSL)
    parse_config, load_directory, WorkflowScriptParser, WorkflowConfigVisitor,
)
from urban_workflow.templating import ( # urban-json (JSLT templates)
    JsltActionTranslator, TemplateRegistry, MetadataRegistry,
)
from urban_workflow.outputs import default_memory_output
from urban_workflow.scripts import ScriptRegistry   # AS @script methods
from urban_workflow.storage_sql import ( # [sql] extra
    SqlWorkflowStorage, sql_output,
)
```

`dsl`, `templating` and `storage_sql` are deliberately not re-exported by
the package root: you only pay their import cost when you use them.
