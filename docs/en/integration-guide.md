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
rules.add("EstComplet", lambda ctx, champs: all(
    ctx.incoming_event.extended_datas.get(c) is not None
    for c in champs.split(",")
))
rules.add("MontantInferieur", lambda ctx, seuil: float(
    ctx.incoming_event.extended_datas.get("Montant", 0)
) < seuil)

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
    "Name": "DemandeSoumise",
    "Uuid": "4f6c6c6f-0000-4000-8000-000000000001",
    "ExternalId": "DA-2026-0042",     # the identifier of the handled subject
    "EventDate": "2026-11-03T10:00:00+00:00",
    "Type": "achat",                  # consumed by MATCHING
    "Montant": 120,                   # business data
})

dossier = storage.get_by(Workflow, "DA-2026-0042", "external_id")[0]
print(dossier.current_state)          # "Approuvee" (120 < seuil_auto)
```

This quick start only uses code rules. §9 assembles the **whole** path
(schemas, rule scripts, JSON artifact, message templates) in a complete
example that runs as is.

## 2. Business rules

A rule is a callable `(ctx, **kwargs) -> bool`. The first parameter is
always the `RunContext`; the rest are the DSL call's named arguments,
already resolved (literals converted to the declared type, `@…` paths read
from the context, constants substituted).

```python
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("MontantInferieur")
def montant_inferieur(ctx: RunContext, seuil: float) -> bool:
    montant = ctx.incoming_event.extended_datas.get("Montant")
    return montant is not None and float(montant) < seuil
```

What the context exposes:

| Attribute | Content |
|---|---|
| `ctx.incoming_event` | The incoming event (`name`, `external_id`, `event_date`, `extended_datas` = the payload) |
| `ctx.workflow` | The instance (`current_state`, `events` = history, `extended_datas` = business state written by `STORE`) |
| `ctx.event` | The event being integrated (`from_state`, `to_state`) |
| `ctx.workflow.states` | The state instances already recorded in the history (`StateInstance`: `name`, `uuid`, `creation_date`, `event_id`), one per `SWITCH` |
| `ctx.pending_states` | The instances created by the `SWITCH`es of the current evaluation, not yet recorded (a `RECURSIVE` rule already sees them) |
| `ctx.functional_log` | Rule-evaluation journal (audit) |

To read the most recent instance of a state (what the DSL calls
`@state`), `urban_workflow.values.find_state_instance(ctx, "StateName")`
searches both lists. An instance's business fields (`extended_datas`) are
**always empty** for now: how they are computed has not been designed yet.

Call validation (`WHEN MontantInferieur(seuil = …)`) runs against the
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
    .add_script("montant_inferieur", "@IncomingEvent.Montant < seuil")
    .add_function("solvable", lambda ctx, client: verifier(client))  # Python
)
config = parse_config(script, rules=rules, schemas=schemas, scripts=scripts)
```

A file's language comes from its extension (`.expr` = `expression`
language); `add_function` registers a `(ctx, **params)` callable whose
signature is checked against the declaration. Another language is added
with `register_language` (a `ScriptLanguage` subclass: `name`,
`extensions`, `check`, `compile`). Details: [rules-guide.md](rules-guide.md).

`.jslt` files (`jslt` language, urban-json) produce **JSON artifacts**
(`DEFINE ARTIFACT … USING @script`), data handed to actions through
`@artifact.Name`. JSON that does not match the artifact's schema raises an
`ArtifactError` and aborts the processing:
[artifacts-guide.md](artifacts-guide.md).

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
    # A fresh visitor per script, with ALL the registries: a visitor
    # without schemas= accepts AS @… references without validating anything,
    # and without scripts= rejects AS @script rules and @artifact paths.
    return WorkflowConfigVisitor(rules=rules, schemas=schemas, scripts=scripts)

configs = load_directory(WorkflowsConfig(), visitor_factory, "workflows/", "*.wf")
```

`FRAGMENT` files are visited before the scripts that `INCLUDE` them; each
full script becomes a document of `configs`. `parse_directory(path,
pattern)` only returns the parsers (syntax), without building the
configurations.

### Fine-grained control

```python
from urban_workflow.dsl import WorkflowScriptParser, WorkflowConfigVisitor

parser = WorkflowScriptParser.parse_string(script_text, filename="x.wf")
parser.check()                 # raises DslSyntaxError on syntax errors
parser.includes                # declared INCLUDE files
parser.is_fragment             # FRAGMENT script?
config = parser.visit(WorkflowConfigVisitor(rules=rules, schemas=schemas, scripts=scripts))
```

`parse_config(source, rules=None, filename="", schemas=None, scripts=None)`
does these three steps in one go.

### Reading and rewriting a script (surface model)

A tool that edits workflows (the playground diagram, for instance) works
on the **surface model**: states, transitions and declarations as data,
guards and `EXECUTE`/`STORE` blocks as raw DSL text.

```python
from urban_workflow.dsl import SurfaceModel, extract_surface, render_script

model = extract_surface(script_text, filename="x.wf")   # DslSyntaxError, SurfaceError
data = model.to_dict()                                   # JSON-compatible
texte = render_script(SurfaceModel.from_dict(data))      # canonical script
```

`render_script` validates nothing: pass the text back to `parse_config`.
`--` comments are not preserved, and a `FRAGMENT` script or one with
`INCLUDE` raises `SurfaceError`.

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
metadatas = MetadataRegistry(default={"canal": "bus-achats"})
metadatas.add_metadata("NotifierValideur", {"canal": "mail", "ttl": "3600"})

processor = WorkflowProcessor(
    configs, WorkflowFactory(),
    translator=JsltActionTranslator(templates, metadatas),
)
```

### `.jslt` templates

One file per action name (`NotifierValideur.jslt`), `default.jslt` as the
fallback. A template navigates the action's **context document**:

```jslt
{
    "Ordre":     "notifier",
    "Niveau":    $.action.arguments.niveau,
    "Dossier":   $.workflow.external_id,
    "Etat":      $.workflow.state,
    "Montant":   $.incoming.Montant,
    "EmisLe":    $.now
}
```

Available sections: `$.action` (uuid, name, kind, delay, resolved
arguments), `$.workflow` (uuid, name, version, external_id, state +
extended data), `$.event` (uuid, name, from_state, to_state + data),
`$.incoming` (uuid, name, external_id, dates + payload), `$.now`.

Without a dedicated template or `default.jslt`, the built-in default
template produces the source engine's historical shape: `Uuid`, `Name`,
`PushedAt`, `Arguments`, `WorkflowId`, `EventId`, `From_State`,
`To_State`. `TemplateRegistry(default_template=…)` replaces it (JSLT
text), or removes it with `None`: an action without a template then
raises an error.

Custom urban-json functions can be exposed to templates:

```python
from urban_json import default_registry

functions = default_registry.copy()
functions.register("majuscules", lambda ctx, v: str(v).upper())
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
2. `processor.output_actions`: a **factory** (a function without
   arguments) that returns a fresh chain on each evaluation.

A link derives from `OutputAction` and receives the next link as an
argument (`child`). Its cycle, for each evaluation:

| Method | Called | Role |
|---|---|---|
| `_prepare_impl(ctx)` | once per impacted context | decide what has to be done, store it in `self.items` (nothing irreversible here) |
| `_begin_transaction_impl()` | once, before execution | return a `Transaction` (an empty transaction by default) |
| `_execute_impl()` | once, under the transaction | do the work |

A `Transaction` implements `_commit_impl()` and `_rollback_impl()`; the
chain's transactions are chained together and committed or rolled back
**together**:

```python
import json

from urban_workflow import OutputAction, Transaction
from urban_workflow.outputs import SetPropertiesOutputAction, PushModelOutputAction

class RabbitTransaction(Transaction):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        channel.tx_select()                  # AMQP: messages kept pending
    def _commit_impl(self):
        self.channel.tx_commit()
    def _rollback_impl(self):
        self.channel.tx_rollback()

class PushToRabbit(OutputAction):
    def __init__(self, channel, child=None):
        super().__init__(child)
        self.channel = channel
    def _prepare_impl(self, ctx):
        self.items.extend(a for a in ctx.event.actions if a.kind == "$_push")
    def _begin_transaction_impl(self):
        return RabbitTransaction(self.channel)
    def _execute_impl(self):
        for action in self.items:
            self.channel.basic_publish("", "workflow",
                                       json.dumps(action.execute_message))

processor.output_actions = lambda: SetPropertiesOutputAction(   # 1. STORE
    PushToRabbit(channel,                                       # 2. bus
                 PushModelOutputAction(storage)))               # 3. persistence
```

Keep `SetPropertiesOutputAction` first: it is the link that applies the
`STORE`s to the workflow; without it, they are lost. For a bus without
transactions, `BusOutputAction(bus, kinds=("$_push",), child=…)` (in
`urban_workflow.outputs`) pushes to any `OutputBus` (a `push(action)`
method) without writing a link.

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

`engine.evaluate_event(payload, incoming_type=None)` accepts JSON
(string), a dict, or an already-built `IncomingEvent`, and returns the
list of impacted `RunContext`s (one per affected workflow; an empty list
if none). Recognised properties (CamelCase, inherited from the source
format):

| Key | Role |
|---|---|
| `Name` | Event name (required for routing) |
| `Uuid` | Event identity — **the replay-without-duplicates key**. Absent or `null`, it is generated, and the event is then deduplicated on its functional signature |
| `ExternalId` | Subject identifier: groups instances |
| `CreationDate`, `EventDate` | ISO 8601 dates. `EventDate` is the **functional date**: it is part of the default deduplication key |
| `DedupKey` | Optional idempotency key supplied by the emitter — two events carrying the same key are integrated only once (takes precedence over `UNIQUE`) |
| `IntegrationDate` | **Set by the engine** (`WorkflowClock`) when `evaluate_event` receives the event: the date it entered the system. A value sent by the emitter is ignored. Kept in the history (`Event.integration_date`, SQL column `integration_date`) and exposed to templates (`event.integration_date`, `incoming.integration_date`) |
| *everything else* | Business data (`extended_datas`), visible to rules, `MATCHING` filters and templates |

An invalid payload raises `InvalidIncomingEventFormatError`.

Deduplication is always on, even without a `DedupKey` or a `UNIQUE`
clause: the payload's `Uuid` is then used as the key, and failing that
the functional signature `Name` + `EventDate` (+ `ExternalId` when set).
An event with neither `Uuid` **nor** `EventDate` is not deduplicated —
the full cascade and the reasoning behind that last case are in
[dsl-guide.md](dsl-guide.md#how-the-engine-picks-the-deduplication-key).
An `IncomingEvent` built in code carries `uuid_from_payload=False`: its
`Uuid` is only used as a key if the caller sets that flag to true.

### Event schemas (`[schemas]` extra)

Schemas (JSON Schema **written in YAML**) live apart from the scripts and
are loaded **when the engine is initialised** — from a file, a directory
or raw content:

```python
from urban_workflow.schemas import SchemaRegistry

schemas = (
    SchemaRegistry()
    .add_directory("schemas/")                 # one .yaml per schema
    .add_file("schemas/commun.yaml", name="schema_Commun")
    .add_yaml("schema_Ping", "type: object")   # raw content
)
config = parse_config(script, rules=rules, schemas=schemas)
```

A schema's name (the file name by default) is the one the DSL references:
`DEFINE EVENT X '…' AS @schema_X;`. An unknown reference is a positioned
error at load time; a non-conforming payload at run time raises
`EventSchemaError` (full list of violations in `exc.errors`). The common
base is validated in addition to the business schema, unless
`SchemaRegistry(include_base=False)`. Without a registry, `AS` references
are kept but nothing is validated (permissive mode).

`add_directory(path, pattern="*.yaml")` only reads `.yaml` files by
default: a `.yml` file is silently ignored (pass `pattern="*.yml"`).
`add_schema(name, dict)` registers an already-loaded schema.

`pip install urban-workflow[schemas]` (PyYAML + jsonschema).

### Locking

The engine serialises the processing of a given subject: the key is
locked during evaluation.

```python
engine = WorkflowEngine(
    processor,
    locker=MonVerrouRedis(),                        # default: MemoryLocker()
    thread_safe_key=lambda event: event.external_id,  # default: the ExternalId
)
```

`MemoryLocker` only protects one process; a distributed lock implements
`LockObject` (`lock(crc)`, `unlock(crc)` on the key's CRC32 fingerprint).
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
    .add_document(parse_config(script_achats_v1, rules=rules))
    .add_document(parse_config(script_achats_v2, rules=rules))
    .add_document(parse_config(script_conges, rules=rules))
)

# New "CircuitAchats" instances are only created on v2;
# existing v1 instances keep running on their own configuration.
configs.set_version_selector("CircuitAchats", 2)
```

`WorkflowFactory(context_factory=MonContexte)` makes the engine create a
`RunContext` subclass (to give Python rules application-specific
services), and `context_initializer=function` is called on every created
context.

Event routing: `MATCHING` filters select the workflows candidate for
**creation**; **existing** instances are found by `ExternalId` and handled
with their original version's configuration. One event can therefore
impact several workflows at once.

## 8. Errors

All exceptions derive from `WorkflowError` and are imported from
`urban_workflow.exceptions` (the most common ones also from the package
root).

**At load time** (`parse_config`, `load_directory`, `WorkflowConfigVisitor`) —
the script is rejected, with a `file:line:column` position:

| Exception | Cause |
|---|---|
| `DslSyntaxError` | syntax error, in the workflow or in a script (`expression`, `jslt`); `exc.errors` lists each positioned error |
| `InvalidMethodReferenceError` | unregistered rule, undeclared action (`DEFINE ACTION`) |
| `InvalidArgumentNameError`, `MissingArgumentNameError` | unknown or missing argument in a rule or action call |
| `InvalidArgumentValueError` | literal not convertible to the declared type; invalid `@` path (absent from the schema, `@state` outside a state, `@artifact` unknown or outside an action's arguments) |
| `DuplicatedArgumentNameError` | duplicate: argument, parameter, declaration (state, event, constant, artifact), initializer, `UNIQUE` property |
| `UnknownSchemaError` | `AS @schema` absent from the `SchemaRegistry` |
| `UnknownScriptError` | `AS @script` or `USING @script` absent from the `ScriptRegistry` |
| `MissingStateError` | `SWITCH` target does not exist, or branch without `SWITCH` |

**At processing time** (`engine.evaluate_event`) — the event is not
integrated, the output transaction is rolled back, and it can be replayed:

| Exception | Cause |
|---|---|
| `InvalidIncomingEventFormatError` | unreadable payload (invalid JSON, malformed dates…) |
| `EventSchemaError` | payload not conforming to the base or to the event's schema; `exc.errors` |
| `ArtifactError` | artifact script failed, or produced JSON not conforming to its schema; `exc.errors` |
| `LockFailedError` | subject lock not acquired |
| `MissingConfigurationError` | workflow or version not found for an existing instance |

A rule, on the other hand, never raises: an `expression` script that meets
a missing value or a value of the wrong type evaluates to `NULL`, hence
`False`.

## 9. Complete end-to-end example

An order workflow that puts together everything above: an event validated
by its schema, a rule written as a script, an action whose body is a
**JSON artifact** produced by a `jslt` script and validated by its schema,
and the message template of that action. The usual files (`.wf`,
`schemas/*.yaml`, `scripts/*.expr|.jslt`, `templates/*.jslt`) are strings
here so that the example runs as is (`pip install urban-workflow[schemas]`).

```python
import json

from urban_workflow import (
    FunctionRegistry, MemoryStorage, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import ArtifactError, EventSchemaError
from urban_workflow.outputs import default_memory_output
from urban_workflow.schemas import SchemaRegistry
from urban_workflow.scripts import ScriptRegistry
from urban_workflow.templating import (
    JsltActionTranslator, MetadataRegistry, TemplateRegistry,
)

# --- The workflow (usually a commandes.wf file) --------------------------
WORKFLOW = """
NAME Commandes VERSION 1

DEFINE EVENT  CommandeValidee 'commande validée' AS @schema_CommandeValidee;
DEFINE EVENT  Livree          'commande livrée';

DEFINE RULE   GrosMontant (DECIMAL seuil) 'montant au-dessus du seuil'
    AS @gros_montant;

DEFINE ACTION AppelerFacturation (TEXT corps) 'appel du service de facturation';
DEFINE ACTION AlerterCommercial (TEXT client)  'alerte commerciale';

DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;

DEFINE CONST  devise       'EUR' 'devise de facturation';
DEFINE CONST  seuil_alerte 1000  'alerte commerciale au-dessus de ce montant';

INITIALIZE WORKFLOW
    ON EVENT CommandeValidee RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage'
    ON EVENT CommandeValidee
        WHEN GrosMontant(seuil = seuil_alerte)
            EXECUTE AlerterCommercial(client = @IncomingEvent.Client.Nom)
            SWITCH Facturee
        SWITCH Facturee
;

DEFINE STATE Facturee 'facture demandée'
    ON ENTER STATE
        EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)
    ON EVENT Livree
        SWITCH Livree
;

DEFINE STATE Livree 'commande livrée';
"""

# --- The schemas (usually schemas/*.yaml) --------------------------------
schemas = (
    SchemaRegistry()
    .add_yaml("schema_CommandeValidee", """
type: object
required: [Client, Montant]
properties:
  Client:
    type: object
    required: [Nom]
    properties:
      Nom: {type: string}
  Montant: {type: number}
""")
    .add_yaml("schema_RequeteFacture", """
type: object
required: [reference, client, montant, devise]
properties:
  reference: {type: string}
  client:    {type: string}
  montant:   {type: number, exclusiveMinimum: 0}
  devise:    {type: string, enum: [EUR]}
""")
)

# --- The scripts (usually scripts/*.expr and scripts/*.jslt) -------------
scripts = (
    ScriptRegistry()
    .add_script("gros_montant", "@IncomingEvent.Montant > seuil")
    .add_script("requete_facture", """{
    "reference": $.Workflow.ExternalId,
    "client":    $.IncomingEvent.Client.Nom,
    "montant":   $.IncomingEvent.Montant,
    "devise":    $.constants.devise
}""", language="jslt")
)

# --- The message of each action (usually templates/*.jslt) ---------------
templates = TemplateRegistry().add_template("AppelerFacturation", """{
    "methode": "POST",
    "url":     "https://facturation.exemple/api/factures",
    "corps":   $.action.arguments.corps
}""")
metadatas = MetadataRegistry(default={"canal": "bus-commandes"})

# --- Loading: every reference is checked here ----------------------------
config = parse_config(WORKFLOW, rules=FunctionRegistry("rule"),
                      schemas=schemas, scripts=scripts, filename="commandes.wf")

# --- Engine assembly -----------------------------------------------------
storage = MemoryStorage()
processor = WorkflowProcessor(
    WorkflowsConfig().add_document(config), WorkflowFactory(),
    translator=JsltActionTranslator(templates, metadatas),
)
processor.load_existing_workflows_by_external_id = (
    lambda key: storage.get_by(Workflow, key, "external_id")
)
processor.output_actions = default_memory_output(storage)
engine = WorkflowEngine(processor)

# --- Processing ----------------------------------------------------------
engine.evaluate_event({
    "Name": "CommandeValidee",
    "Uuid": "c0000000-0000-4000-8000-000000000001",
    "ExternalId": "CMD-1",
    "Client": {"Nom": "ACME"},
    "Montant": 1500,
})

commande = storage.get_by(Workflow, "CMD-1", "external_id")[0]
print(commande.current_state)
for action in commande.last_event.actions:
    print(action.name, json.dumps(action.execute_message, ensure_ascii=False))

# --- The two processing errors -------------------------------------------
try:   # the payload does not match schema_CommandeValidee (Client missing)
    engine.evaluate_event({"Name": "CommandeValidee", "ExternalId": "CMD-2",
                           "Uuid": "c0000000-0000-4000-8000-000000000002",
                           "Montant": 10})
except EventSchemaError as exc:
    print("refusé :", exc.errors)

try:   # the produced artifact does not match schema_RequeteFacture (montant 0)
    engine.evaluate_event({"Name": "CommandeValidee", "ExternalId": "CMD-3",
                           "Uuid": "c0000000-0000-4000-8000-000000000003",
                           "Client": {"Nom": "Durand"}, "Montant": 0})
except ArtifactError as exc:
    print("interrompu :", exc.errors)
print(storage.get_by(Workflow, "CMD-3", "external_id"))
```

Output (identifiers and dates shortened):

```
Facturee
AlerterCommercial {"Header": {"canal": "bus-commandes"}, "Body": {"Uuid": "…", "Name": "AlerterCommercial", "PushedAt": "…", "Arguments": {"client": "ACME"}, "WorkflowId": "…", "EventId": "c0000000-…-000000000001", "From_State": "Tri", "To_State": "Facturee"}}
AppelerFacturation {"Header": {"canal": "bus-commandes"}, "Body": {"methode": "POST", "url": "https://facturation.exemple/api/factures", "corps": {"reference": "CMD-1", "client": "ACME", "montant": 1500, "devise": "EUR"}}}
refusé : ["<racine>: 'Client' is a required property"]
interrompu : ['montant: 0 is less than or equal to the minimum of 0']
[]
```

Key points:

- **everything is checked at load time**: a misspelt schema, script, rule
  or artifact name, an `@IncomingEvent.Client.Nom` path absent from the
  schema, a syntax error in a script, all reject the workflow before the
  first event;
- `AlerterCommercial` has no template: it gets the default body
  (`Arguments`, `WorkflowId`…); `AppelerFacturation` gets its own, which
  puts the artifact under `corps`;
- CMD-3 left **no trace** (last line): the invalid artifact aborted the
  processing before anything was written.

What the system consuming the messages does with the `AppelerFacturation`
message (the HTTP call itself) is outside the engine: the engine
guarantees the body is well formed, then pushes it into the output chain
(§5).

## 10. Import summary

```python
from urban_workflow import (            # core, no heavy dependency
    FunctionRegistry, RunContext, Workflow, IncomingEvent, PushedAction,
    WorkflowsConfig, WorkflowFactory, WorkflowProcessor, WorkflowEngine,
    MemoryStorage, MemoryLocker, LockObject, OutputAction, Transaction,
    WorkflowClock, constants,
)
from urban_workflow.dsl import (        # ANTLR parser (the DSL)
    parse_config, load_directory, parse_directory,
    WorkflowScriptParser, WorkflowConfigVisitor,
)
from urban_workflow.templating import ( # urban-json (JSLT templates)
    JsltActionTranslator, TemplateRegistry, MetadataRegistry,
)
from urban_workflow.outputs import (
    default_memory_output, SetPropertiesOutputAction, PushBusOutputAction,
    PushModelOutputAction, BusOutputAction, OutputBus,
)
from urban_workflow.schemas import SchemaRegistry        # [schemas] extra
from urban_workflow.scripts import ScriptRegistry        # AS/USING @… scripts
from urban_workflow.artifacts import JsltLanguage, produce_artifact
from urban_workflow.values import find_state_instance
from urban_workflow.exceptions import (                  # §8
    WorkflowError, DslSyntaxError, EventSchemaError, ArtifactError,
    UnknownSchemaError, UnknownScriptError,
)
from urban_workflow.storage_sql import SqlWorkflowStorage, sql_output  # [sql] extra
```

`dsl` and `templating` are sub-packages deliberately not re-exported by
the package root: you only pay their import cost when you use them.
