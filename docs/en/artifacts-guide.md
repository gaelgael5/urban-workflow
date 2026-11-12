# JSON artifacts guide

*[Français](../guide-artefacts.md) · English*

An **artifact** is a **named** JSON document, produced on demand from the
workflow context so that it can be **handed to something else**: the body
of an HTTP call, a message to another system, a file to drop. Producing
JSON is not the goal in itself: the artifact guarantees that an action
receives **well-formed** data.

```sql
DEFINE ARTIFACT RequeteFacture 'body of the billing request'
    AS @schema_RequeteFacture USING @requete_facture;

DEFINE STATE Facturee 'invoice requested'
    ON ENTER STATE
        EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)
;
```

```
// scripts/requete_facture.jslt
{
    "reference": $.Workflow.ExternalId,
    "client":    { "nom": $.IncomingEvent.Client.Nom },
    "lignes":    $.IncomingEvent.Lignes,
    "montant":   $.IncomingEvent.Montant,
    "devise":    $.constants.devise
}
```

## 1. Principle

An artifact brings three things together:

| Element | Where | Role |
|---|---|---|
| the **name** and label | `DEFINE ARTIFACT` in the workflow | what actions reference |
| the **production script** | `USING @script`, in the `ScriptRegistry` | builds the JSON from the context (usually the `jslt` language) |
| the **schema** (optional) | `AS @schema`, in the `SchemaRegistry` | validates the produced JSON, as for events and states |

As with rules, the workflow document holds no code: it references the
script, which lives alongside it (see [rules-guide.md](rules-guide.md)).

## 2. Declaring an artifact

```sql
DEFINE ARTIFACT Name 'label' [AS @schema] USING @script;
```

- `AS @schema` is optional. Without a schema, the produced JSON is not
  checked.
- `USING @script` is required.
- An artifact has **no parameters**: its script reads the context (incoming
  event, state, workflow, constants).
- Artifacts have their own namespace: an artifact may share its name with a
  rule or an action.

## 3. Consuming an artifact: `@artifact.Name`

An artifact is read through the `@artifact.Name` path in the **arguments of
an `EXECUTE` action**:

```sql
EXECUTE AppelerFacturation(corps  = @artifact.RequeteFacture,
                           client = @artifact.RequeteFacture.client.nom)
```

- `@artifact.Name` gives the whole JSON; `@artifact.Name.part` (or `[0]`
  for a list element) gives only part of it.
- The artifact is produced when the action message is built, then validated
  against its schema. It travels down the **output chain** with the action,
  in the message's `Body.Arguments`.
- It is not available anywhere else (arguments of a `WHEN` rule, scripts):
  it is data handed to an action, not a condition.

## 4. The `jslt` language

`.jslt` scripts are [urban-json](https://github.com/gaelgael5/Jslt) (JSLT)
transformations: the script text **is** the shape of the produced JSON,
with values taken from the input document through `$.…` paths.

### The input document

| Path | Content | DSL equivalent |
|---|---|---|
| `$.IncomingEvent` | the incoming event, wire format (common base + business data) | `@IncomingEvent` |
| `$.state` | the most recent instance of the state of the block using the artifact (`Name`, `Uuid`, `CreationDate`, `EventId`, business fields); `null` outside a `DEFINE STATE` | `@state` |
| `$.Workflow` | `Uuid`, `ExternalId`, `CurrentState`, `WorkflowName`, `Version` and the instance's extended data | `@Workflow` |
| `$.constants` | the workflow's `DEFINE CONST` | constants |
| `$.now` | the engine time (`WorkflowClock`), in ISO 8601 format | `NOW()` |

A missing path gives `null`, without an error. The schema decides whether a
missing value is acceptable.

### Examples

```
{
    "commande": $.Workflow.ExternalId,
    "etat":     $.state.Name,
    "depuis":   $.state.CreationDate,
    "total":    $.IncomingEvent.Montant * 1.2,
    "texte":    "Votre commande est livrée",
    "client":   upper($.IncomingEvent.Client.Nom)
}
```

urban-json's built-in functions (`upper`, `lower`, `trim`, `format`,
`round`, `sum`, `uuid`, `sha256`…) are available. Custom functions are added
with `JsltLanguage(functions=registry)` (see §6).

A script may also be written in another language of the registry: an
`expression` script produces a value (`@IncomingEvent.Montant * 2`), and a
Python function registered with `add_function` returns JSON.

## 5. Checks and errors

**At load time** (`parse_config`), with `file:line:column` positions:

- an unknown script or schema is reported on the `USING @…` or `AS @…`
  reference;
- a JSLT syntax error is positioned **inside the script**, as soon as it is
  registered (`requete_facture.jslt:3:12`);
- `@artifact.Unknown` is rejected, and so is `@artifact.X.part` when `part`
  does not exist in the artifact's schema;
- `@artifact.…` is rejected outside the arguments of an action;
- an artifact declared twice is rejected.

**During processing**, an `ArtifactError` is raised when:

- the script fails (unknown function, impossible operation);
- the produced JSON does not match the schema. The message lists the
  violations (`montant: 0 is less than or equal to the minimum of 0`), and
  `exc.errors` gives them one by one.

The error **aborts the processing of the event**, and the output
transaction is rolled back. This is deliberate, and the opposite of a rule
(which gives `False` rather than failing): malformed data must not silently
reach the system waiting for it.

**Without a registry**: when `parse_config` receives no `scripts`, the
declarations are kept (references unresolved), but `@artifact.X` is
rejected, since there is nothing to produce the artifact with. Without
`schemas`, the `AS @…` reference is kept and nothing is validated.

## 6. In code

```python
from urban_workflow.dsl import parse_config
from urban_workflow.schemas import SchemaRegistry
from urban_workflow.scripts import ScriptRegistry

scripts = ScriptRegistry().add_directory("scripts/")   # .jslt, .expr…
schemas = SchemaRegistry().add_directory("schemas/")
config = parse_config(workflow_text, schemas=schemas, scripts=scripts)
```

The `jslt` language is provided by default (`urban-json` is already a
dependency of the engine). To give it custom functions:

```python
from urban_json import default_registry
from urban_workflow.artifacts import JsltLanguage
from urban_workflow.dsl.expressions import ExpressionLanguage
from urban_workflow.scripts import PythonLanguage, ScriptRegistry

functions = default_registry.copy()
functions.register("iban_masque", lambda ctx, iban: "****" + iban[-4:])
scripts = ScriptRegistry(languages=[
    ExpressionLanguage(), PythonLanguage(), JsltLanguage(functions=functions),
])
```

To produce an artifact outside an action (preview, test, host code), with
the same script, the same document and the same validation:

```python
from urban_workflow.artifacts import produce_artifact

json_value = produce_artifact(
    config, "RequeteFacture", scripts, run_ctx,
    state_name="Facturee", constants={"devise": "EUR"},
)
```

The `TemplateRegistry` of action messages (§4 of
[integration-guide.md](integration-guide.md)) is a **separate** mechanism:
it shapes the message envelope, whereas the artifact is data passed as an
argument.

## 7. In the playground

- In the editor, `USING @` suggests scripts, `AS @` suggests schemas, and
  `@artifact.` suggests artifacts along with the parts known from their
  schema.
- The **Scripts** view edits `jslt` scripts. It suggests the `$.…` paths of
  the input document and urban-json's functions, and underlines syntax
  errors inside the script.
- **Preview**: below the editor, « Produire le JSON » applies the script and
  the schema to a sample event (the first one of the simulation, which you
  can edit), in the chosen state. By default, this is the state where the
  artifact is used.
- The simulation shows the artifact inside the action message. A schema
  violation shows up as an error on the event concerned.
- The « Artefacts JSON » example shows two artifacts, one validated by a
  schema and one without, with one order that matches the schema and one
  that does not.
