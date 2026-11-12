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
NAME MonWorkflow VERSION 1
CONCURENCY 1
DESCRIPTION 'ce que fait ce workflow'
MATCHING (Type = 'achat')

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
**Strings**: single quotes, `''` escapes a quote (`'l''événement'`).

## 2. The header

```sql
NAME ValidationAchat VERSION 2
CONCURENCY 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat' Pays = 'France')
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
zero-downtime migration mechanism: deploy v2, pin creations to v2, let the
v1 cases in progress finish on v1.

### Routing with `MATCHING`

Several different workflows can be loaded in the same engine. When an event
arrives, only those whose `MATCHING` filter is satisfied are candidates for
creation:

```sql
-- file achats.wf
NAME CircuitAchats
MATCHING (Type = 'achat')
…

-- file conges.wf
NAME CircuitConges
MATCHING (Type = 'conge')
…
```

An event `{ "Type": "achat", … }` only creates instances of
`CircuitAchats`.

## 3. The referential (`DEFINE`)

Each declaration ends with `;`. **At least one declaration is required**
per script. Using an undeclared name, an unknown or missing argument, or
any duplicate, is a **positioned** error (`file:line:column`) raised at
load time — never at run time.

### Events

```sql
DEFINE EVENT DemandeSoumise 'une demande est déposée'
    AS @schema_DemandeSoumise UNIQUE (ExternalId, Montant);
```

Declares a business event the workflow accepts. A received but undeclared
event is ignored by this workflow. Two optional clauses (urban-workflow
extensions):

- **`AS @name`** — references a **JSON Schema written in YAML**, registered
  separately and loaded when the engine is initialised (see
  [integration-guide.md](integration-guide.md) §6); every incoming event
  of that name is then validated against the common base (`Name`, `Uuid`,
  `ExternalId`, `CreationDate`, `EventDate`, `DedupKey`,
  `IntegrationDate` — the latter set by the engine) **and** against this
  schema — a non-conforming payload raises `EventSchemaError`;
- **`UNIQUE (Prop, …)`** — functional deduplication: the engine hashes the
  concatenation of these payload properties (SHA-256) and **ignores** any
  event whose fingerprint already exists in the workflow history (same
  silent mechanism as the `Uuid` anti-replay).

#### How the engine picks the deduplication key

Deduplication is **always on**: with no explicit key, the engine falls
back to the event's base properties. First matching rule wins, from the
most explicit to the fallback:

| # | Key used | When |
|---|---|---|
| 1 | `DedupKey` | the emitter supplies this reserved property (idempotency key) |
| 2 | the `UNIQUE (…)` properties | configured on `DEFINE EVENT` |
| 3 | `Uuid` | neither of the above, but the payload carries a non-null `Uuid` |
| 4 | `Name` + `EventDate` (+ `ExternalId` when set) | neither of the above, and no `Uuid` in the payload |
| — | *none* (nothing is deduplicated) | no `Uuid` **and** no `EventDate` |

Case 4 is the event's **functional signature**: same type, same
functional date, same case file = same event. `ExternalId` enters the
fingerprint when set, so that two different case files do not
deduplicate against each other.

The last case is deliberate: `Name` (+ `ExternalId`) alone would reject
*every* later event of the same type on the same case file. Too broad a
deduplication silently drops events, whereas its absence at worst lets a
duplicate through — so an event with neither `Uuid` nor `EventDate` needs
a `UNIQUE` or a `DedupKey` to be deduplicated.

A caller that builds an `IncomingEvent` itself instead of passing a
payload sets `uuid_from_payload=True` for its `Uuid` to be used as the
key (case 3): without that flag, the default generated `Uuid` would be
indistinguishable from a meaningful one.

### Rules

```sql
DEFINE RULE MontantInferieur (DECIMAL seuil) 'le montant est sous le seuil';
```

A rule is a **business predicate** used in `WHEN` conditions. Its signature
(`TEXT`, `INTEGER`, `DECIMAL`) types the arguments: a `'500'` literal passed
to a `DECIMAL` parameter reaches Python as a `float`. The implementation is
either a Python callable registered under the same name (see
[integration-guide.md](integration-guide.md) §2), or a **referenced
script** (below).

#### Rules implemented by a script (`AS @script`)

urban-workflow extension: the workflow document carries no code. A rule
**references** its method, written next to it and loaded at engine start
into a `ScriptRegistry`, like schemas:

```sql
DEFINE RULE MontantInferieur (DECIMAL seuil) 'le montant est sous le seuil'
    AS @montant_inferieur;
```

```sql
-- montant_inferieur.expr
@IncomingEvent.Montant < seuil
```

The rule is called exactly like a code rule
(`WHEN MontantInferieur(seuil = seuil_auto)`); the script uses the typed
parameters of the declaration. The script language is chosen at load time:
the `expression` language (`.expr` files: comparisons, `IN`, `IS NULL`,
arithmetic, `NOW()`, `DAYS_BETWEEN`…), a Python function, or any
registered language. A rule has a script OR a code function under its
name, never both. An unknown script name is rejected at load time.

Full reference (languages, `expression` language, `NULL` semantics,
checks): [rules-guide.md](rules-guide.md).

### Actions

```sql
DEFINE ACTION NotifierValideur (TEXT niveau) 'demande d''approbation';
DEFINE ACTION Archiver (TEXT dossier) 'archivage' AS @archiver;
```

An action is a **message pushed outward** (bus, queue, API…) when the
workflow triggers it. Unlike rules, it has no Python implementation: its
materialisation into JSON goes through a template (see
[integration-guide.md](integration-guide.md) §4).

urban-workflow extension: an action may also reference a method
(`AS @script`), for the same reason as rules. The reference is checked at
load time; executing action methods is still to be designed (no effect
today).

Rules and actions share the same namespace: declaring `RULE X` then
`ACTION X` is an error.

### Artifacts

```sql
DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;
```

urban-workflow extension: an artifact is a **named** JSON document,
produced by a script (`USING @…`, usually `jslt`) and validated by an
optional schema (`AS @…`). It hands well-formed data to an action:
`EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)`. No
parameters: the script reads the context. Details:
[artifacts-guide.md](artifacts-guide.md).

### Constants

```sql
DEFINE CONST seuil_auto 500          'seuil d''approbation automatique';
DEFINE CONST service    'achats'     'nom du service';
DEFINE CONST relance    2 DAY        'délai de relance';
```

A constant is then referenced **by its bare name** inside an argument:
`MontantInferieur(seuil = seuil_auto)`. Possible values: string, number,
delay (`n MINUTE|HOUR|DAY`, converted to minutes), identifier.

## 4. Call arguments

In `rule(arg = …)` as in `action(arg = …)`, a value takes one of three
forms:

| Form | Example | Semantics |
|---|---|---|
| Literal | `motif = 'dossier incomplet'` | Fixed value, converted to the declared parameter type |
| `@` path | `cible = @Workflow.ExternalId`, `montant = @IncomingEvent.Montant` | **Lazy reference**, resolved at run time against the context |
| Bare name | `seuil = seuil_auto` | `DEFINE CONST` constant if it exists, otherwise a text literal |

### `@` paths

A path navigates the execution context, segment by segment:

- `@Workflow.…` — the instance: `Uuid`, `ExternalId`, `CurrentState`,
  `WorkflowName`, `Version`, plus any key of its extended data (whatever
  `STORE` wrote there, plus the creating event's data);
- `@IncomingEvent.…` — the **incoming event** (see below);
- `@state.…` — the **current state instance** (see below);
- `@artifact.Name[.part]` — a **JSON artifact** produced on demand, only in
  the arguments of an action ([artifacts-guide.md](artifacts-guide.md));
- `@Event.…` — legacy path to the event being written to the history,
  kept for existing scripts but no longer suggested: the source and target
  states are not event properties (one event may be processed by several
  workflows in parallel); the state references the event instead
  (`@state.EventId`).

Paths accept the DSL's CamelCase even though the Python attributes are
snake_case (`@Workflow.ExternalId` → `workflow.external_id`), falling back
to extended data when the segment is not an attribute.

### `@IncomingEvent` and `@state`: JSON documents

These two roots point to **documents** — the same objects as in the
playground's Events and States views and in the schema YAML — and accept,
in addition to `.Prop`, list indexes `[n]` and keys `['name']` (a name
that is not an identifier, or a keyword):

```
DEFINE STATE Tri 'aiguillage' AS @schema_Tri
    ON EVENT DemandeSoumise
        WHEN MontantInferieur(seuil = @IncomingEvent.Montant)
         AND PaysAutorise(pays = @IncomingEvent.Client.Pays)
         AND QuantiteValide(qte = @IncomingEvent.Lignes[0].Qte)
        SWITCH EnValidation
```

- **`@IncomingEvent`**: the document event schemas validate — base
  (`Name`, `Uuid`, `ExternalId`, `CreationDate`, `EventDate`, `DedupKey`,
  `IntegrationDate` set by the engine) plus payload business data. It
  carries nothing workflow-specific.
- **`@state`**: the instance of the state whose `DEFINE STATE` block you
  are writing in — base `Name`, `Uuid`, `CreationDate` (entry into the
  state), `EventId` (the event that created the instance) plus the state
  schema's fields (declared and checked, but **always absent for now**:
  how they are computed has not been designed yet, so they are `NULL`).
  In `ON EVENT`, it is the current state; in `ON ENTER`, the instance that
  has just been created. **Not available in `INITIALIZE WORKFLOW`** (no
  state exists yet): positioned error.
- `@IncomingEvent` (or `@state`) alone passes the whole document. No
  filters or wildcards: a rule receives **one** value. The value keeps its
  JSON type (no conversion to the declared type). A missing path yields
  `None`: a missing optional field is a normal business case.
- `[n]` / `['name']` segments are only accepted on these two roots.
- **Checked at load time**: if the designated object has a schema
  (`AS @…`) and the engine receives the schema registry, an unknown path
  (`@IncomingEvent.Montnt`, `@state.Decisoin`) is a positioned error
  (`file:line:col`). The check stops without error where the schema cannot
  decide (`$ref`, `allOf`/`anyOf`/`oneOf`, `patternProperties`,
  `additionalProperties` described by a schema).
- In the playground, `@IncomingEvent.` suggests the properties of the
  event of the current `ON EVENT` block, `@state.` those of the state of
  the current `DEFINE STATE` block — business fields first, then the base.

## 5. Creating an instance to handle a subject (`INITIALIZE WORKFLOW`)

This is **the** answer to "a new subject arrives, open a case":

```sql
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise
        WHEN EstComplet(champs = 'Montant')
        SWITCH EnValidation
```

When a `DemandeSoumise` event passes the `MATCHING` filter and its `WHEN`
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
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            SWITCH Incomplete
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        SWITCH EnValidation
;
```

Here the instance is born in `Tri` and the request is immediately routed to
`Incomplete`, `Approuvee` or `EnValidation` according to the rules (two
state instances: `Tri`, then the target).

**Viable switch.** Every switch (initializer or transition, with or
without `RECURSIVE`) only counts if the target state then **offers a
route** for the current event: a passing branch (`WHEN` true or a branch
without `WHEN`), or no `ON EVENT` for that event. If `Tri` handles
`DemandeSoumise` but none of its branches passes, everything happens **as
if that switch had not been met**: no `Tri` instance, no action, the
workflow stays in its current state (or no workflow is created, for an
initializer) and the next branch is tried; the reason is traced in the
functional log. The original .NET engine instead left the instance stuck
in `Tri`, without reporting it.

The route found is only **followed** with `RECURSIVE`; without it, it is
used for the check alone. The look-ahead is one level deep (the target of
the route found is not checked in turn), and the target's guards may be
evaluated twice: rules must stay side-effect-free predicates.
Without `RECURSIVE`, the event is not re-evaluated in the target: no route
check takes place.

## 6. States and transitions (`SWITCH`)

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'

    ON EVENT ValidationAccordee
        SWITCH Approuvee

    ON EVENT ValidationRefusee
        EXECUTE NotifierDemandeur(motif = @IncomingEvent.Motif)
        SWITCH Rejetee
;
```

`DEFINE STATE X 'label' AS @schema_X` (urban-workflow extension) links the
state to the YAML schema of its business fields, in the same registry as
event schemas. The state base (`Name`, `Uuid`, `CreationDate`, `EventId`)
is set by the engine and cannot be redefined. **Computing** a state's
business fields is still to come: today they are modelled (schema, checks,
intellisense).

**A state instance is created every time a `SWITCH` is taken**, even to
the current state (`Approuvee → Approuvee` creates a new instance), with a
fresh `Uuid`, its entry date and the `Uuid` of the event that created it.
Instances are kept in the workflow history (`workflow.states`, SQL table
`workflow_states`).

An `ON EVENT name` block lists **branches** (`switch_state`). When the
event arrives, branches are evaluated **in order**; the **first** whose
`WHEN` holds (or which has no `WHEN`) is applied, the rest are ignored. A
branch can:

- change state (`SWITCH target`) — the target must exist, checked at load
  time;
- run actions before changing state (`EXECUTE … SWITCH …`).

**Every branch ends with a `SWITCH`.** The grammar accepts a branch made
only of actions, but the engine rejects it at load time
(`MissingStateError: missing state name`). To run actions without changing
state, switch to the current state:

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT Relance
        EXECUTE NotifierValideur(niveau = 'relance', dossier = @Workflow.ExternalId)
        SWITCH EnValidation        -- stays in the state (new state instance)
;
```

A trailing branch without `WHEN` acts as the **default case**.

### `WHEN` conditions

A condition combines rule calls with `NOT`, `AND`, `OR` and parentheses:

```sql
WHEN (EstComplet(champs = 'Montant') AND NOT MontantInferieur(seuil = seuil_auto))
     OR EstUrgent(niveau = @IncomingEvent.Priorite)
```

Every rule evaluation is traced in the context's functional log
(`IsMajor(agemin=18) -> True`), making the engine's decisions auditable.

### Use case: an approval flow

The complete "submission → review → approval/rejection, with incomplete
file and follow-up" pattern:

```sql
NAME ValidationAchat VERSION 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise     'une demande est déposée';
DEFINE EVENT  PiecesFournies     'le demandeur complète son dossier';
DEFINE EVENT  ValidationAccordee 'un valideur approuve';
DEFINE EVENT  ValidationRefusee  'un valideur refuse';

DEFINE RULE   EstComplet (TEXT champs)         'les champs requis sont présents';
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil';

DEFINE ACTION NotifierValideur (TEXT niveau, TEXT dossier)  'demande d''approbation';
DEFINE ACTION NotifierDemandeur (TEXT motif, TEXT dossier)  'information du demandeur';

DEFINE CONST  seuil_auto 500 'approbation automatique sous ce montant';

INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            EXECUTE NotifierDemandeur(motif = 'dossier incomplet',
                                      dossier = @Workflow.ExternalId)
            SWITCH Incomplete
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        EXECUTE NotifierValideur(niveau = 'standard',
                                 dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;

DEFINE STATE Incomplete 'en attente de pièces'
    ON EVENT PiecesFournies
        WHEN EstComplet(champs = 'Montant')
            EXECUTE NotifierValideur(niveau = 'standard',
                                     dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;

DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        SWITCH Approuvee
    ON EVENT ValidationRefusee
        EXECUTE NotifierDemandeur(motif = @IncomingEvent.Motif,
                                  dossier = @Workflow.ExternalId)
        SWITCH Rejetee
    EXPIRE AFTER 3 DAY
        SWITCH Expiree
;

DEFINE STATE Approuvee 'demande approuvée'
    ON ENTER STATE
        STORE (Statut = 'approuvee')
;

DEFINE STATE Rejetee 'demande rejetée'
    ON ENTER STATE
        STORE (Statut = 'rejetee')
;

DEFINE STATE Expiree 'validation expirée sans réponse'
    ON ENTER STATE
        EXECUTE NotifierValideur(niveau = 'relance',
                                 dossier = @Workflow.ExternalId)
;
```

## 7. Triggering actions

### `EXECUTE` — push a message

```sql
EXECUTE NotifierValideur(niveau = 'standard', dossier = @Workflow.ExternalId)
```

Produces an action of kind `$_push`, materialised as a JSON message (via
its template) and pushed on the output bus. Several calls can follow each
other in the same branch.

### Custom kind

```sql
audit NotifierValideur(niveau = 'trace')
```

Replacing the `EXECUTE` keyword with an identifier produces the action with
that kind (`audit` here) instead of `$_push` — useful to route some actions
differently in the output chain.

### `STORE` — write into the workflow data

```sql
STORE (Statut = 'approuvee' Etape = 'fin')
```

Produces `$_update` actions that write the pairs into the **instance's
extended data**. These values are then readable through `@Workflow.Statut`
paths and by host code.

### `ON ENTER STATE` / `ON EXIT STATE`

Actions attached to **entering** or **leaving** a state, whatever the
transition that leads there:

```sql
DEFINE STATE Approuvee 'demande approuvée'
    ON ENTER STATE
        WHEN NotifActive(canal = 'mail')
            EXECUTE NotifierDemandeur(motif = 'approbation', dossier = @Workflow.ExternalId)
    ON EXIT STATE
        EXECUTE Auditer(etape = 'sortie-approuvee')
    ON ENTER AND EXIT STATE
        EXECUTE Tracer(etat = 'Approuvee')
;
```

Each block accepts an optional `WHEN`. During a transition, collection
order is: event actions, transition actions, `ON EXIT` of the left state,
`ON ENTER` of the reached state.

### `WAITING … BEFORE` — deferring an action

```sql
ON ENTER STATE
    WAITING 10 MINUTE BEFORE
    EXECUTE NotifierValideur(niveau = 'rappel', dossier = @Workflow.ExternalId)
```

The action is pushed **wrapped in a reminder message** (`$_reminder`)
carrying the delay in minutes: the host infrastructure (deferred reminder
bus) replays it when due. Units: `MINUTE`, `HOUR`, `DAY`.

## 8. State expiry (`EXPIRE AFTER`)

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        SWITCH Approuvee
    EXPIRE AFTER 3 DAY
        SWITCH Expiree
;
```

`EXPIRE AFTER` wires the complete expiry cycle:

1. **on entering** the state, a deferred `__expired` reminder (3 days here)
   is pushed on the reminder bus;
2. **on leaving** the state through another transition, a reminder cancel
   action (`__cancelReminderAction`) is pushed;
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
-- referentiel.wf
FRAGMENT NAME referentiel
DESCRIPTION 'déclarations communes du domaine achats'
DEFINE EVENT DemandeSoumise 'une demande est déposée';
DEFINE RULE  EstComplet (TEXT champs) 'les champs requis sont présents';
DEFINE CONST seuil_auto 500 'seuil d''approbation automatique';
```

and imported by every full script:

```sql
-- validation.wf
INCLUDE 'referentiel.wf'
NAME ValidationAchat VERSION 1
DEFINE ACTION NotifierValideur (TEXT niveau) 'demande d''approbation';
…
```

When loading a directory, fragments are resolved by file name and visited
before the script that includes them: their declarations are available as
if they were local.

## 10. Errors

Loading fails early, with positioned messages (`file:line:column`):

| Error | Typical cause |
|---|---|
| `DslSyntaxError` | Invalid syntax, missing `;` — each error carries file, line, column; also for a syntax error **in a script** (`montant_eleve.expr:2:5`) |
| `InvalidMethodReferenceError` | `EXECUTE Inconnue(…)` without `DEFINE ACTION`, or `WHEN RegleNonEnregistree(…)` |
| `InvalidArgumentNameError` | Argument not in the declared signature |
| `MissingArgumentNameError` | Declared parameter not provided |
| `DuplicatedArgumentNameError` | Duplicate: argument, parameter, declaration (state, event, constant, artifact), initializer, state event, `UNIQUE` property |
| `InvalidArgumentValueError` | `'abc'` passed to an `INTEGER` parameter; `@IncomingEvent.X` path absent from the schema; `@state` in `INITIALIZE WORKFLOW`; `@artifact.Inconnu` |
| `MissingStateError` | `SWITCH EtatInexistant`, or branch without `SWITCH` |
| `UnknownSchemaError` | `AS @schema` absent from the `SchemaRegistry` |
| `UnknownScriptError` | `AS @script` or `USING @script` absent from the `ScriptRegistry` |

While an event is being processed, two language-specific errors abort the
integration (the event can be replayed):

| Error | Cause |
|---|---|
| `EventSchemaError` | the payload does not match the event's schema (`AS @schema`) |
| `ArtifactError` | the JSON produced by an artifact does not match its schema, or its script fails |

All inherit from `WorkflowError` and are imported from
`urban_workflow.exceptions`; the complete list, including the engine
errors, is in §8 of [integration-guide.md](integration-guide.md).

## 11. Cheat sheet

```sql
NAME nom VERSION n                        -- identity
CONCURENCY n                              -- max instances per subject
DESCRIPTION 'libellé'
MATCHING (K = 'v' …)                      -- event routing

DEFINE EVENT  Nom 'libellé' [AS @schema] [UNIQUE (Prop, …)];
DEFINE RULE   Nom (TYPE arg, …) 'libellé';     -- TYPE: TEXT|INTEGER|DECIMAL
DEFINE RULE   Nom (TYPE arg, …) 'libellé' AS @script;      -- method in the ScriptRegistry
DEFINE ACTION Nom (TYPE arg, …) 'libellé';
DEFINE ARTIFACT Nom 'libellé' [AS @schema] USING @script;   -- JSON read by @artifact.Nom
DEFINE CONST  nom valeur 'libellé';            -- value: 'txt' | 42 | n DAY

INITIALIZE WORKFLOW
    ON EVENT Nom [WHEN cond] [RECURSIVE] SWITCH Etat

DEFINE STATE Etat 'libellé'
    ON ENTER STATE | ON EXIT STATE | ON ENTER AND EXIT STATE
        [WHEN cond] [WAITING n UNITE BEFORE] actions
    ON EVENT Nom
        [WHEN cond] [actions] SWITCH Cible     -- in-order branches, the 1st true one wins
    EXPIRE AFTER n UNITE
        [WHEN cond] [actions] SWITCH Cible
;

-- actions:
EXECUTE Action(arg = 'litteral', arg2 = @Chemin.Compose, arg3 = constante)
monkind Action(…)                         -- custom kind
STORE (Cle = 'valeur' …)                  -- writes into @Workflow.Cle

-- conditions:
WHEN Regle(a = 1) AND (NOT Autre(b = 'x') OR Tierce(c = @IncomingEvent.K))
```

**Reserved words** — forbidden as event, state, rule… names when written
in upper case (keywords are case-sensitive: `Etat` or `state` remain
free): `ACTION`, `AFTER`, `AND`, `ARTIFACT`, `AS`, `BEFORE`, `CONCURENCY`, `CONST`, `DAY`, `DECIMAL`, `DEFINE`, `DESCRIPTION`, `ENTER`, `EVENT`, `EXECUTE`, `EXIT`, `EXPIRE`, `FALSE`, `FRAGMENT`, `HOUR`, `IN`, `INCLUDE`, `INITIALIZE`, `INTEGER`, `IS`, `MATCHING`, `MINUTE`, `NAME`, `NOT`, `NULL`, `ON`, `OR`, `PARAMETER`, `RECURSIVE`, `RULE`, `STATE`, `STORE`, `SWITCH`, `TEXT`, `TIME`, `TRUE`, `UNIQUE`, `USING`, `VERSION`, `WAITING`, `WHEN`, `WITH`, `WORKFLOW`. `PARAMETER`, `TIME` and `WITH` are reserved by the
grammar without being used today.
