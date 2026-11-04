# Language guide — creating a workflow

An urban-workflow workflow is a **state machine** declared in a text file,
using a SQL-flavoured dedicated language. This document is the complete
language reference: every construct, its syntax, its semantics and its use
cases.

> The Python side (engine, business rules, output templates) is covered in
> [integration-guide.md](integration-guide.md); writing rules and testing in
> [testing-guide.md](testing-guide.md). Version française :
> [../guide-dsl.md](../guide-dsl.md).

## 1. Overview

A script describes:

1. the workflow **identity** (name, version, description);
2. the **routing**: which incoming events concern it (`MATCHING`);
3. the **referential**: the events, rules, actions and constants in use
   (`DEFINE …`) — everything is declared before being used, and the parser
   validates every usage at build time;
4. the **creation**: which event creates a workflow instance to handle a
   new subject (`INITIALIZE WORKFLOW`);
5. the **states** and their transitions (`DEFINE STATE … ON EVENT … SWITCH`).

Complete skeleton:

```sql
NAME MyWorkflow VERSION 1
CONCURENCY 1
DESCRIPTION 'what this workflow does'
MATCHING (Type = 'purchase')

DEFINE EVENT  …;        -- referential: at least one declaration required
DEFINE RULE   …;
DEFINE ACTION …;
DEFINE CONST  …;

INITIALIZE WORKFLOW     -- instance creation
    ON EVENT … SWITCH …

DEFINE STATE …          -- one block per state, ended by ;
;
```

Section order is enforced by the grammar: header, declarations,
`INITIALIZE WORKFLOW`, then the states.

**Comments**: `-- to end of line` and `/* block */`.
**Strings**: single quotes, `''` escapes a quote (`'it''s'`).

## 2. The header

```sql
NAME PurchaseValidation VERSION 2
CONCURENCY 1
DESCRIPTION 'purchase request approval flow'
MATCHING (Type = 'purchase' Country = 'France')
```

| Clause | Role | Default |
|---|---|---|
| `NAME name` | Workflow identifier (required) | — |
| `VERSION n` | Version of this configuration | `1` |
| `CONCURENCY n` | Maximum simultaneous instances for the same subject (same `ExternalId`) | `1` |
| `DESCRIPTION '…'` | Human-readable label | empty |
| `MATCHING (key = 'value' …)` | Routing filter: the incoming event must carry **all** these pairs in its data for this workflow to be a candidate | no filter |

### Versioning a workflow

Several scripts may share the same `NAME` with different `VERSION`s and be
loaded together. An instance **created** with version 1 lives on
configuration 1; **new** instances can be restricted to a given version on
the code side (`WorkflowsConfig.set_version_selector`). This is the
zero-downtime migration mechanism: deploy v2, pin creations to v2, let v1
instances finish on v1.

### Routing with `MATCHING`

Several different workflows can be loaded in the same engine. When an event
arrives, only those whose `MATCHING` filter is satisfied are candidates for
creation. An event `{ "Type": "purchase", … }` only creates instances of
workflows whose filter matches.

## 3. The referential (`DEFINE`)

Each declaration ends with `;`. **At least one declaration is required**
per script. Using an undeclared name, an unknown or missing argument, or
declaring a duplicate, is a **positioned** error
(`file:line:column`) raised at load time — never at run time.

### Events

```sql
DEFINE EVENT RequestSubmitted 'a request is filed';
```

Declares a business event the workflow accepts. A received but undeclared
event is ignored by this workflow.

### Rules

```sql
DEFINE RULE AmountBelow (DECIMAL threshold) 'amount is below the threshold';
```

A rule is a **business predicate** used in `WHEN` conditions. Its signature
(`TEXT`, `INTEGER`, `DECIMAL`) types the arguments: a `'500'` literal passed
to a `DECIMAL` parameter reaches Python as a `float`. The implementation is
a Python callable registered under the same name (see
[integration-guide.md](integration-guide.md) §2).

### Actions

```sql
DEFINE ACTION NotifyApprover (TEXT level) 'approval request';
```

An action is a **message pushed outward** (bus, queue, API…) when the
workflow triggers it. Unlike rules, it has no Python implementation: its
materialisation into JSON goes through a template (see
[integration-guide.md](integration-guide.md) §4).

Rules and actions share the same namespace: declaring `RULE X` then
`ACTION X` is an error.

### Constants

```sql
DEFINE CONST auto_threshold 500      'auto-approval threshold';
DEFINE CONST department 'purchasing' 'department name';
DEFINE CONST follow_up   2 DAY       'follow-up delay';
```

A constant is then referenced **by its bare name** inside an argument:
`AmountBelow(threshold = auto_threshold)`. Possible values: string, number,
delay (`n MINUTE|HOUR|DAY`, converted to minutes), identifier.

## 4. Call arguments

In `rule(arg = …)` as in `action(arg = …)`, a value takes one of three
forms:

| Form | Example | Semantics |
|---|---|---|
| Literal | `reason = 'incomplete file'` | Fixed value, converted to the declared parameter type |
| `@` path | `target = @Workflow.ExternalId` | **Lazy reference**, resolved at run time against the context |
| Bare name | `threshold = auto_threshold` | `DEFINE CONST` constant if it exists, otherwise a text literal |

### `@` paths

A path navigates the execution context, segment by segment:

- `@Workflow.…` — the instance: `Uuid`, `ExternalId`, `CurrentState`,
  `WorkflowName`, `Version`, plus any key of its extended data (whatever
  `STORE` wrote there, plus the creating event's data);
- `@IncomingEvent.…` — the incoming event: `Name`, `Uuid`, `ExternalId`,
  `EventDate`, plus any payload key (`@IncomingEvent.Amount`);
- `@Event.…` — the event being integrated into the history: `Name`,
  `FromState`, `ToState`, plus the data copied from the incoming event.

Paths accept the DSL's CamelCase even though the Python attributes are
snake_case (`@Workflow.ExternalId` → `workflow.external_id`), falling back
to extended data when the segment is not an attribute.

## 5. Creating an instance to handle a subject (`INITIALIZE WORKFLOW`)

This is **the** answer to "a new subject arrives, open a case":

```sql
INITIALIZE WORKFLOW
    ON EVENT RequestSubmitted
        WHEN IsComplete(fields = 'Amount')
        SWITCH UnderReview
```

When a `RequestSubmitted` event passes the `MATCHING` filter and its `WHEN`
condition holds, an instance is created, identified by the event's
`ExternalId` (the case, customer or order number…), and placed in the
`SWITCH` state. Payload data is copied into the instance's extended data.

Semantics:

- **one initialisation path per event name** — to route to different states
  depending on conditions, use the "dispatch state + `RECURSIVE`" pattern
  below;
- `CONCURENCY` caps the number of simultaneous instances of the same
  workflow for one `ExternalId`; beyond it, the event creates no more;
- an already-integrated event (same `Uuid`) never creates a duplicate
  (replays are no-ops).

### `RECURSIVE`: chaining a transition immediately

Without `RECURSIVE`, the instance is created in the target state and waits
for the next event. With `RECURSIVE`, **the same event is immediately
re-evaluated** in the target state, allowing create *and* route in one
move:

```sql
INITIALIZE WORKFLOW
    ON EVENT RequestSubmitted RECURSIVE SWITCH Dispatch

DEFINE STATE Dispatch 'routing at creation'
    ON EVENT RequestSubmitted
        WHEN NOT IsComplete(fields = 'Amount')
            SWITCH Incomplete
        WHEN AmountBelow(threshold = auto_threshold)
            SWITCH Approved
        SWITCH UnderReview
;
```

The instance is born in `Dispatch` and the request is immediately routed to
`Incomplete`, `Approved` or `UnderReview` according to the rules.

## 6. States and transitions (`SWITCH`)

```sql
DEFINE STATE UnderReview 'waiting for an approver'

    ON EVENT ApprovalGranted
        SWITCH Approved

    ON EVENT ApprovalDenied
        EXECUTE NotifyRequester(reason = @IncomingEvent.Reason)
        SWITCH Rejected
;
```

An `ON EVENT name` block lists **branches**. When the event arrives,
branches are evaluated **in order**; the **first** whose `WHEN` holds (or
which has no `WHEN`) is applied, the rest are ignored. A branch can:

- change state (`SWITCH target`) — the target must exist, checked at load
  time;
- run actions before switching (`EXECUTE … SWITCH …`);
- run actions **without changing state** (branch without `SWITCH`).

A trailing branch without `WHEN` acts as the **default case**.

### `WHEN` conditions

A condition combines rule calls with `NOT`, `AND`, `OR` and parentheses:

```sql
WHEN (IsComplete(fields = 'Amount') AND NOT AmountBelow(threshold = auto_threshold))
     OR IsUrgent(level = @IncomingEvent.Priority)
```

Every rule evaluation is traced in the context's functional log
(`IsMajor(agemin=18) -> True`), making the engine's decisions auditable.

### Use case: an approval flow

See the full worked example (submission → review → approval/rejection, with
incomplete file handling and expiry follow-up) in the French guide
[../guide-dsl.md](../guide-dsl.md) §6 — kept in one place because it is
executed verbatim by the test suite (`tests/test_docs_examples.py`).

## 7. Triggering actions

### `EXECUTE` — push a message

```sql
EXECUTE NotifyApprover(level = 'standard', case = @Workflow.ExternalId)
```

Produces an action of kind `$_push`, materialised as a JSON message (via
its template) and pushed on the output bus.

### Custom kind

```sql
audit NotifyApprover(level = 'trace')
```

Replacing the `EXECUTE` keyword with an identifier produces the action with
that kind (`audit` here) instead of `$_push` — useful to route some actions
differently in the output chain.

### `STORE` — write into the workflow data

```sql
STORE (Status = 'approved' Step = 'done')
```

Produces `$_update` actions that write the pairs into the **instance's
extended data**. These values are then readable through `@Workflow.Status`
paths and by host code.

### `ON ENTER STATE` / `ON EXIT STATE`

Actions attached to **entering** or **leaving** a state, whatever the
transition:

```sql
DEFINE STATE Approved 'request approved'
    ON ENTER STATE
        WHEN NotificationEnabled(channel = 'mail')
            EXECUTE NotifyRequester(reason = 'approved', case = @Workflow.ExternalId)
    ON EXIT STATE
        EXECUTE Audit(step = 'leaving-approved')
    ON ENTER AND EXIT STATE
        EXECUTE Trace(state = 'Approved')
;
```

Each block accepts an optional `WHEN`. During a transition, collection
order is: event actions, transition actions, `ON EXIT` of the left state,
`ON ENTER` of the reached state.

### `WAITING … BEFORE` — deferring an action

```sql
ON ENTER STATE
    WAITING 10 MINUTE BEFORE
    EXECUTE NotifyApprover(level = 'reminder', case = @Workflow.ExternalId)
```

The action is pushed **wrapped in a reminder message** (`$_reminder`)
carrying the delay in minutes: the host infrastructure (deferred reminder
bus) replays it when due. Units: `MINUTE`, `HOUR`, `DAY`.

## 8. State expiry (`EXPIRE AFTER`)

```sql
DEFINE STATE UnderReview 'waiting for an approver'
    ON EVENT ApprovalGranted
        SWITCH Approved
    EXPIRE AFTER 3 DAY
        SWITCH Expired
;
```

`EXPIRE AFTER` wires the complete expiry cycle:

1. **on entering** the state, a deferred `__expired` reminder (3 days here)
   is pushed on the reminder bus;
2. **on leaving** the state through another transition, a cancel action
   (`__cancelReminderAction`) is pushed;
3. when the reminder comes back as an **`__expired`** event (carried by the
   infrastructure, with `WorkflowId` and `CurrentState`), the expiry
   transition applies — **only if the state has not changed** meanwhile: a
   stale reminder is ignored.

An extra `WHEN` on the expiry branch combines (AND) with this automatic
guard.

## 9. Reusable fragments (`FRAGMENT` / `INCLUDE`)

A referential shared by several workflows (same events, rules, constants)
is declared once in a **fragment**:

```sql
-- referential.wf
FRAGMENT NAME referential
DESCRIPTION 'shared purchasing declarations'
DEFINE EVENT RequestSubmitted 'a request is filed';
DEFINE RULE  IsComplete (TEXT fields) 'required fields are present';
DEFINE CONST auto_threshold 500 'auto-approval threshold';
```

and imported by every full script:

```sql
-- validation.wf
INCLUDE 'referential.wf'
NAME PurchaseValidation VERSION 1
DEFINE ACTION NotifyApprover (TEXT level) 'approval request';
…
```

When loading a directory, fragments are resolved by file name and visited
before the script that includes them: their declarations behave as local.

## 10. Parser errors

Loading fails early, with positioned messages:

| Error | Typical cause |
|---|---|
| `DslSyntaxError` | Invalid syntax, missing `;` — each error carries file, line, column |
| `InvalidMethodReferenceError` | `EXECUTE Unknown(…)` without `DEFINE ACTION`, or `WHEN UnregisteredRule(…)` |
| `InvalidArgumentNameError` | Argument not in the declared signature |
| `MissingArgumentNameError` | Declared parameter not provided |
| `DuplicatedArgumentNameError` | Duplicate declaration, parameter, argument, state, or state event |
| `InvalidArgumentValueError` | `'abc'` passed to an `INTEGER` parameter |
| `MissingStateError` | `SWITCH NonexistentState` |

All inherit from `WorkflowError`.

## 11. Cheat sheet

```sql
NAME name VERSION n                       -- identity
CONCURENCY n                              -- max instances per subject
DESCRIPTION 'label'
MATCHING (K = 'v' …)                      -- event routing

DEFINE EVENT  Name 'label' [AS @schema] [UNIQUE (Prop, …)];
DEFINE RULE   Name (TYPE arg, …) 'label';      -- TYPE: TEXT|INTEGER|DECIMAL
DEFINE ACTION Name (TYPE arg, …) 'label';
DEFINE CONST  name value 'label';              -- value: 'txt' | 42 | n DAY

INITIALIZE WORKFLOW
    ON EVENT Name [WHEN cond] [RECURSIVE] SWITCH State

DEFINE STATE State 'label'
    ON ENTER STATE | ON EXIT STATE | ON ENTER AND EXIT STATE
        [WHEN cond] [WAITING n UNIT BEFORE] actions
    ON EVENT Name
        [WHEN cond] [actions] [SWITCH Target]  -- in-order branches, first true wins
    EXPIRE AFTER n UNIT
        [WHEN cond] [actions] SWITCH Target
;

-- actions:
EXECUTE Action(arg = 'literal', arg2 = @Composite.Path, arg3 = constant)
mykind Action(…)                          -- custom kind
STORE (Key = 'value' …)                   -- writes @Workflow.Key

-- conditions:
WHEN Rule(a = 1) AND (NOT Other(b = 'x') OR Third(c = @IncomingEvent.K))
```
