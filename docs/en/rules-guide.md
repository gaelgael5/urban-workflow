# Guide to rules written in the DSL

> Reference of the rule expression language (`DEFINE RULE … AS …`). The
> rest of the DSL is in [dsl-guide.md](dsl-guide.md); Python rules in
> [integration-guide.md](integration-guide.md) §2.

## 1. Principle

A rule is a **business predicate** used by `WHEN` conditions. It can be
implemented in two ways, with **the same call syntax**:

| | Code rule | Rule written in the DSL |
|---|---|---|
| Declaration | `DEFINE RULE R (DECIMAL threshold) 'l';` | `DEFINE RULE R (DECIMAL threshold) 'l' AS <expression>;` |
| Implementation | Python callable registered in the `FunctionRegistry` | the expression after `AS` |
| Call | `WHEN R(threshold = '1000')` | `WHEN R(threshold = '1000')` |

Use the DSL for conditions that are **readable by the business** and
**side-effect free**: comparing amounts, checking a channel, measuring the
age of a state. Keep Python for external calls, database access or
algorithmic logic.

A rule has a body **or** a registered function, never both: the same name
with a body and a code function is rejected at load time.

## 2. Writing a rule

```sql
DEFINE RULE HighAmount (DECIMAL threshold) 'amount above the threshold'
    AS @IncomingEvent.Amount > threshold;
```

- The signature (`TEXT`, `INTEGER`, `DECIMAL`) types the parameters: a
  `'1000'` argument passed to a `DECIMAL` reaches the expression as a
  number.
- The label is optional, as for any rule.
- The expression ends at the `;`.

### Several lines and comments

**The body may span as many lines as needed.** Line breaks, spaces and
comments (`-- …` to the end of the line, multi-line `/* … */`) are allowed
anywhere between `AS` and `;`, including inside an `IN` list or function
arguments:

```sql
DEFINE RULE Eligible (DECIMAL threshold, INTEGER days) 'eligible for fast track'
    AS -- a loyal customer counts double
       (@IncomingEvent.Amount * 2 > threshold OR @IncomingEvent.Loyal = TRUE)
       /* digital channels only */
       AND @IncomingEvent.Channel IN ('web',
                                      'mobile')
       AND DAYS_BETWEEN(@state.CreationDate, NOW()) < days;
```

Layout is free: the engine only reads tokens. Recommended convention (also
used by the script generated from the Diagram view): `AS` on its own line,
indented by 4 spaces, following lines aligned under the first element
after `AS`, with `AND`/`OR` leading the line. Errors report the exact line
inside the body.

## 3. What an expression may contain

### Values

| Written | Value |
|---|---|
| `42` | integer |
| `1.5` | decimal (digits required on both sides: `0.5`, not `.5`) |
| `'text'` | text; a quote is written `''`: `'O''Brien'` |
| `TRUE`, `FALSE` | booleans |
| `NULL` | no value |

Negative numbers use unary minus: `-5`.

### References

| Written | Refers to |
|---|---|
| `threshold` | a **parameter** of the rule |
| `urgent_cap` | a `DEFINE CONST` **constant**, even declared after the rule |
| `@IncomingEvent.Amount` | a property of the incoming event (base + payload), with `.Customer.Country`, `[0]`, `['name']` |
| `@state.CreationDate` | the instance of the state of the block where the rule is **called** (base `Name`, `Uuid`, `CreationDate`, `EventId` plus the state schema fields) |
| `@Workflow.ExternalId` | the other `@` paths of the DSL ([dsl-guide.md](dsl-guide.md) §4) |

A parameter hides a constant of the same name. **An unknown bare name is an
error**, unlike call arguments where it becomes text: in a body, text
always takes quotes, so a typo (`treshold`) never silently becomes the
string `'treshold'`.

### Operators

| Family | Operators | Example |
|---|---|---|
| arithmetic | `-x`, `*`, `/`, `+`, `-` | `@IncomingEvent.Amount * 1.2 > cap` |
| comparison | `=`, `!=` (or `<>`), `<`, `<=`, `>`, `>=` | `LENGTH(@IncomingEvent.Documents) >= minimum` |
| membership | `x IN (a, b, …)`, `x NOT IN (…)` | `@IncomingEvent.Plan IN ('basic', 'premium')` |
| absence | `x IS NULL`, `x IS NOT NULL` | `@IncomingEvent.Amount IS NULL` |
| logic | `NOT`, `AND`, `OR`, parentheses | `NOT (a OR b)` |

**Precedence**, strongest first:

1. unary minus `-x`;
2. `*` `/`;
3. `+` `-`;
4. comparisons, `IN`, `IS NULL`;
5. `NOT`;
6. `AND`;
7. `OR`.

`NOT a = b` reads `NOT (a = b)`, and `a OR b AND c` reads `a OR (b AND c)`.
When in doubt, use parentheses.

`/` is a decimal division: `7 / 2` is `3.5`. `+` between two texts
concatenates them.

Keywords are **uppercase** (`AND`, `IN`, `NULL`…). `IN`, `IS`, `NULL`,
`TRUE` and `FALSE` are reserved words of the DSL and can no longer be used
as names.

### Functions

Function names are case-insensitive (`now()` = `NOW()`).

| Function | Result | Example |
|---|---|---|
| `NOW()` | current date and time (engine clock, `WorkflowClock`) | `@IncomingEvent.DueDate < NOW()` |
| `DAYS_BETWEEN(start, end)` | number of days (decimal) from `start` to `end`; negative if `end` is before `start` | `DAYS_BETWEEN(@state.CreationDate, NOW()) >= 3` |
| `HOURS_BETWEEN(start, end)` | same, in hours | `HOURS_BETWEEN(@IncomingEvent.EventDate, NOW()) < 24` |
| `MINUTES_BETWEEN(start, end)` | same, in minutes | |
| `LENGTH(x)` | length of a text, list or object; `NULL` otherwise | `LENGTH(@IncomingEvent.Documents) >= 2` |
| `CONTAINS(container, item)` | text: substring; list: item present; object: key present | `CONTAINS(@IncomingEvent.Title, 'urgent')` |

An unknown function or a wrong argument count is rejected at load time.

## 4. Semantics: a rule never makes processing fail

A malformed event must not stop the engine. Unexpected data yields a value,
never an exception:

| Situation | Result |
|---|---|
| property missing from the document (`@IncomingEvent.Missing`) | `NULL` |
| ordering comparison (`<`, `>`…) with `NULL` or incompatible types (`5 > 'a'`) | false |
| `=` between different types (`5 = '5'`) | false; `!=` true |
| arithmetic with `NULL`, incompatible types or division by zero | `NULL`, which makes the following comparison false |
| `NULL` read by `AND`, `OR` or `NOT` | false (so `NOT x` is true when `x` is `NULL`) |
| `x IN (…)` with `x` being `NULL` | true only if the list contains `NULL` |

Worth knowing: `NOT (@IncomingEvent.Amount > 100)` is **true** when
`Amount` is missing. To require presence, write
`@IncomingEvent.Amount IS NOT NULL AND @IncomingEvent.Amount <= 100`.

**No implicit conversion of event data.** Values keep their JSON type: an
amount sent as text (`"Amount": "1500"`) is not a number, and `> 1000` is
false. Guaranteeing types is the job of the event schema (`AS @schema`).

**Dates.** In documents, dates are ISO 8601 texts (`2026-11-05T10:00:00Z`).
They are converted to dates as soon as the other side of a comparison is a
date (`NOW()`), and by the `*_BETWEEN` functions. Two texts are compared as
texts. A date without time zone compared to one with a time zone gives
false (or `NULL` for a difference).

## 5. Load-time checks

The script is rejected, with a positioned error (`file:line:column`), if:

- the body has a syntax error;
- it uses a name that is neither a parameter nor a constant;
- it calls an unknown function, or with a wrong argument count;
- the rule has both a body and a code function of the same name;
- a call omits a declared parameter, or passes an unknown one.

The body is then **recompiled at each call site**, in the context of the
calling block:

- `@state` is the state of the `DEFINE STATE` holding the call; it is
  rejected when the rule is called in `INITIALIZE WORKFLOW` (no state
  exists yet);
- an `@IncomingEvent.…` path is checked against the schema of the event of
  the calling `ON EVENT` block, when a schema registry is provided.

The error then points into the body and quotes the call:
`… (in rule 'CanRemind' called at workflow.wf:24:12)`. The same rule may be
valid when called in one state and rejected in another.

## 6. Execution and log

Each evaluation is traced in the workflow log like a code rule, with the
argument values:

```
HighAmount(threshold=1000.0) -> True
```

**A rule must have no side effect.** The engine may evaluate it several
times for the same event: to check that a switch is viable, it evaluates
the guards of the target state in advance. Rules written in the DSL have,
by construction, no way to change anything.

## 7. Examples

```sql
-- Thresholds and arithmetic
DEFINE CONST urgent_cap 5000 'urgent handling cap';
DEFINE RULE Urgent (DECIMAL cap) 'urgent claim'
    AS CONTAINS(@IncomingEvent.Title, 'urgent')
       OR @IncomingEvent.Amount * 1.2 > cap;

-- List of values
DEFINE RULE KnownPlan () 'plan in the catalogue'
    AS @IncomingEvent.Plan IN ('basic', 'premium', 'pro');

-- Missing data
DEFINE RULE NoAmount () 'amount not provided'
    AS @IncomingEvent.Amount IS NULL;

-- Age of the current state (to be called inside a DEFINE STATE)
DEFINE RULE Old (INTEGER days) 'in the state long enough'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= days;

-- Commitment in months, computed in days
DEFINE RULE CommitmentOver (INTEGER months) 'commitment period over'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= months * 30;
```

Calls:

```sql
DEFINE STATE Triage 'triage'
    ON EVENT Claim
        WHEN Urgent(cap = urgent_cap) SWITCH Priority
    ON EVENT Reminder
        WHEN Old(days = '3') SWITCH InProgress
```

The playground ships two complete examples to replay: « Règles écrites
dans le script » and « États et switch viable » (Examples menu).

## 8. In the playground

- A rule with a body is really evaluated: it needs no entry in the
  Settings panel. A panel rule with the same name is ignored and shown
  struck through.
- Inside a body, completion (`Ctrl`+`Space`) offers the rule parameters,
  constants, functions, `@IncomingEvent.`, `@state.` and operators.
- Errors are underlined on the exact line of the body.
