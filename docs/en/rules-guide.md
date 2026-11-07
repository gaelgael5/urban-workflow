# Guide to rules and their scripts

> How a DSL rule references its method (`DEFINE RULE … AS @script`), how
> to load scripts, and the reference of the `expression` language. The
> rest of the DSL is in [dsl-guide.md](dsl-guide.md); code rules in
> [integration-guide.md](integration-guide.md) §2.

## 1. Principle: the workflow references, the script implements

The workflow document describes the **business** (states, transitions,
conditions); it carries no code. A rule declares its name, its typed
signature and, with `AS @name`, **the method that implements it**:

```sql
DEFINE RULE HighAmount (DECIMAL threshold) 'amount above the threshold' AS @high_amount;
```

The `high_amount` script lives next to it, in a **script registry** loaded
at engine start, like event schemas:

```sql
-- scripts/high_amount.expr
@IncomingEvent.Amount > threshold
```

This split brings three things:

- **the choice of language** for each method, made at load time: the
  provided `expression` language, a Python function, or any registered
  language. The workflow does not change when the implementation does;
- **reuse**: several rules may reference the same script;
- **uniformity** with actions, which reference their method the same way
  (`DEFINE ACTION … AS @script`, see §2).

| Declaration | Implementation looked up |
|---|---|
| `DEFINE RULE R (…) 'l';` | Python callable registered as `R` in the `FunctionRegistry` (original behaviour) |
| `DEFINE RULE R (…) 'l' AS @name;` | script `name` of the `ScriptRegistry` |

The call is the same in both cases: `WHEN R(threshold = '1000')`. A rule
has a script **or** a code function under its name, never both: loading
rejects that duplicate.

## 2. Referencing a script in the DSL

```sql
DEFINE RULE   Urgent (DECIMAL cap) 'urgent claim' AS @urgent;
DEFINE RULE   Old (INTEGER days) 'in the state for long enough'
    AS @rules.age;
DEFINE ACTION Archive (TEXT file) 'archive the file' AS @archive;
```

- `AS @name` comes after the optional label.
- The name may contain dots (`@rules.age`) to group scripts by theme.
- The script uses the **parameters of the declaration** that references it
  (`cap`, `days`): the declaration fixes their names and types. A `'1000'`
  argument passed to a `DECIMAL` reaches the script as a number.
- **Actions:** the reference is accepted and checked at load time, but
  executing action methods is still to be designed. Today it has no effect
  and the action produces its message as before (JSLT template).

## 3. Loading scripts: the `ScriptRegistry`

```python
from urban_workflow.dsl import parse_config
from urban_workflow.scripts import ScriptRegistry

scripts = (
    ScriptRegistry()
    .add_directory("scripts/")                    # one file per script
    .add_file("common/cap.expr", name="rules.cap")
    .add_script("digital_channel", "@IncomingEvent.Channel IN ('web', 'mobile')")
    .add_function("solvent", lambda ctx, customer: check_solvency(customer))
)
config = parse_config(workflow_text, rules=rules, schemas=schemas, scripts=scripts)
```

| Method | Effect |
|---|---|
| `add_directory(path)` | loads files whose extension matches a known language; others are ignored |
| `add_file(path, name=None)` | loads a file; language = extension, name = file name without extension |
| `add_script(name, text, language="expression")` | registers a script from its text |
| `add_function(name, callable)` | registers a Python callable `(ctx, **params)` |
| `register_language(language)` | adds a language |

**Syntax is checked at registration**: a badly written script raises a
`DslSyntaxError` positioned in its file (`scripts/urgent.expr:2:5`). A name
registered twice is rejected.

### Provided languages

| Language | Source | Behaviour |
|---|---|---|
| `expression` | `.expr` files, or `add_script` | one boolean expression, described in §4 |
| `python` | `add_function` only | the callable receives the context then the named arguments; its signature is checked against the declaration at load time |

The registry never executes `.py` files: loading Python code remains the
application's decision, which then registers its functions.

### Adding a language

A language is a `ScriptLanguage` subclass:

```python
from urban_workflow.scripts import ScriptLanguage

class JsltLanguage(ScriptLanguage):
    name = "jslt"
    extensions = (".jslt",)

    def check(self, script):           # at registration: syntax
        compile_jslt(script.source)

    def compile(self, script, binding):
        # binding.parameters: signature of the referencing declaration
        # binding.constants:  workflow constants
        template = compile_jslt(script.source)
        return lambda run_ctx, params: template.evaluate(run_ctx, params)

scripts = ScriptRegistry().register_language(JsltLanguage()).add_directory("scripts/")
```

`compile` is called **at each call site** of the rule, with the signature
of the declaration: that is where a language checks the names a script
uses.

### Without a registry

If `parse_config` gets no `scripts`, `AS @…` references are kept
unresolved (same permissive mode as schemas). But **calling** a script
rule is then rejected, as nothing can evaluate it: `rule 'R' is
implemented by script @name but no ScriptRegistry was provided`.

## 4. The `expression` language

An `expression` script holds **a single expression**, which gives the
rule's result. A trailing `;` is tolerated.

### Several lines and comments

A script spans as many lines as needed. `-- …` comments (to the end of the
line) and `/* … */` are allowed anywhere:

```sql
-- urgent.expr: claim to handle first
CONTAINS(@IncomingEvent.Title, 'urgent')
    /* amount plus 20 % above the cap */
    OR @IncomingEvent.Amount * 1.2 > cap
```

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
| `threshold` | a **parameter** of the declaration referencing the script |
| `urgent_cap` | a workflow `DEFINE CONST` **constant**, even declared after the rule |
| `@IncomingEvent.Amount` | a property of the incoming event (base + payload), with `.Customer.Country`, `[0]`, `['name']` |
| `@state.CreationDate` | the instance of the state of the block where the rule is **called** (base `Name`, `Uuid`, `CreationDate`, `EventId` plus the state schema fields) |
| `@Workflow.ExternalId` | the other `@` paths of the DSL ([dsl-guide.md](dsl-guide.md) §4) |

A parameter hides a constant of the same name. **An unknown bare name is an
error**, unlike DSL call arguments where it becomes text: in a script,
text always takes quotes, so a typo (`treshold`) never silently becomes
the string `'treshold'`.

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

### Semantics: a rule never makes processing fail

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

On the workflow side, loading is rejected with a positioned error
(`workflow.wf:line:column`) if:

- `AS @name` points to a script missing from the registry;
- a rule has both a script and a code function under its name;
- a call omits a declared parameter, or passes an unknown one.

Each rule script is then checked **against the signature of every
declaration that references it**, even if the rule is never called, and
**recompiled at each call**, in the context of the calling block:

- `@state` is the state of the `DEFINE STATE` holding the call; it is
  rejected when the rule is called in `INITIALIZE WORKFLOW` (no state
  exists yet);
- an `@IncomingEvent.…` path is checked against the schema of the event of
  the calling `ON EVENT` block, when a schema registry is provided.

An error found in a script is positioned **in the script** and quotes the
relevant place of the workflow:

```
scripts/urgent.expr:3:25: unknown identifier 'capp'; parameters: ['cap'], …
    (in rule 'Urgent' declared at workflow.wf:12:50)
scripts/age.expr:1:13: @state is only available inside a DEFINE STATE block …
    (in rule 'Old' called at workflow.wf:31:13)
```

The same script may thus be valid for one rule and rejected for another
(different parameters), or valid when called in a state and rejected in
`INITIALIZE WORKFLOW`.

## 6. Execution and log

Each evaluation is traced in the workflow log like a code rule, with the
argument values:

```
Urgent(cap=5000.0) -> True
```

**A rule must have no side effect.** The engine may evaluate it several
times for the same event: to check that a switch is viable, it evaluates
the guards of the target state in advance. `expression` scripts have, by
construction, no way to change anything; a Python function must follow
the same rule.

## 7. Complete example

Workflow:

```sql
NAME Claims VERSION 1
DEFINE EVENT  ClaimFiled 'a claim is filed' AS @schema_Claim;
DEFINE EVENT  Reminder 'the customer sends a reminder';

DEFINE RULE   Urgent (DECIMAL cap) 'urgent claim' AS @urgent;
DEFINE RULE   Old (INTEGER days) 'in the state for long enough' AS @age;
DEFINE CONST  urgent_cap 5000 'above: priority handling';

INITIALIZE WORKFLOW
    ON EVENT ClaimFiled RECURSIVE SWITCH Triage

DEFINE STATE Triage 'triage'
    ON EVENT ClaimFiled
        WHEN Urgent(cap = urgent_cap) SWITCH Priority
        SWITCH Waiting
;
DEFINE STATE Waiting 'waiting'
    ON EVENT Reminder
        WHEN Old(days = '3') SWITCH Priority
;
DEFINE STATE Priority 'priority' ;
```

Scripts:

```sql
-- scripts/urgent.expr
CONTAINS(@IncomingEvent.Title, 'urgent')
    OR @IncomingEvent.Amount * 1.2 > cap
```

```sql
-- scripts/age.expr: @state = the state of the calling block (Waiting)
DAYS_BETWEEN(@state.CreationDate, NOW()) >= days
```

Loading:

```python
scripts = ScriptRegistry().add_directory("scripts/")
config = parse_config(workflow_text, schemas=schemas, scripts=scripts)
```

## 8. In the playground

- The **Scripts** view lists the scripts referenced by the workflow (rules
  and actions) and those written but unused. Badges: « à écrire » (to
  write), « erreur » (error), « inutilisé » (unused).
- The detail shows the declarations using the script and an editor with
  completion (`Ctrl`+`Space`): parameters of those declarations,
  constants, functions, `@IncomingEvent.…`, `@state.…`, operators. Errors
  are underlined in the script, and also in the workflow at the reference
  or the call.
- « écrire en script », below the list, converts a rule without a script:
  the playground adds `AS @name` to its declaration and creates the script.
- In the workflow editor, `AS @` after a `DEFINE RULE` or `DEFINE ACTION`
  offers script names.
- A script rule needs no entry in the Settings panel. A panel rule with the
  same name is ignored and shown struck through.
- The « Règles et scripts » and « États et switch viable » examples are
  complete and replay as is.
