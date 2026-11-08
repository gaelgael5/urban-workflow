# urban-workflow-playground

*English · [Français](https://github.com/gaelgael5/urban-workflow/blob/v0.2.1/playground/README.md)*

Web components to write, visualize and test
[urban-workflow](https://pypi.org/project/urban-workflow/) workflows, and
the server that provides them with **real** analysis and simulation (ANTLR
parser, visitor, in-memory engine).

The package serves two purposes:

- **the playground**: a ready-to-use page (`urban-workflow-playground`,
  port 8777) that assembles all the components;
- **a client application**: it mounts the components it wants, where it
  wants them (the editor alone, the diagram next to a form, tabs of its
  choosing…), and serves the API from its own FastAPI application.

## Running the playground

```bash
pip install urban-workflow-playground
urban-workflow-playground            # http://127.0.0.1:8777
```

or `python -m urban_workflow_playground`. Variables: `PLAYGROUND_HOST`
(default `127.0.0.1`), `PLAYGROUND_PORT` (default `8777`),
`PLAYGROUND_LAYOUT_DIR` (layout directory, see below).

From a clone of the repository: `pip install -e ./playground`.

## The components

Each component renders into the element it is given and communicates with
the others **only through a shared workspace**. None is mandatory, and
none assumes another one is present.

| Name | What it displays |
|---|---|
| `editor` | workflow text: highlighting, **contextual intellisense** (`Ctrl+Space` or automatic), errors underlined and listed below (option `diagnostics: false` to hide the list) |
| `status` | badge with the result of the last analysis (« script valide » (valid script), « 2 erreur(s) » (2 errors)) |
| `diagram` | editable graphical view (states, transitions, initializers ⚡, expirations ⏰), with its toolbar; « Générer le DSL » (Generate the DSL) writes the canonical script back into the workspace |
| `events` | list of events; for each one, the common base (read-only) and the visual editor of its business schema |
| `states` | the same for states |
| `scripts` | rule scripts (`AS @name`, `expression` language) and artifact scripts (`USING @name`, `jslt` language), with completion, errors inside the script and a preview of the produced JSON; server-side Python functions shown read-only |
| `rules` | **simulated** business rules (code rules do not exist in the browser: name, typed parameters, result) |
| `schemas` | JSON schemas (YAML) of events, states and artifacts, with what uses them |
| `structure` | compiled configuration: initializers, states, transitions |
| `simulation` | JSON events replayed on the real in-memory engine: states reached, actions and their messages, log |
| `help` | language cheat sheet |
| `examples` | drop-down list of examples, which loads the chosen example into the workspace |
| `tabs` | tabbed container of components (optional) |

`UrbanWorkflow.components()` lists the loaded components, with their
label and description.

### Mounting components

A host page loads the dependencies (CodeMirror, X6, the schema editor),
then **a single** components file, `static/urban-workflow.js`, and its
stylesheet:

```html
<link rel="stylesheet" href="/workflow/static/vendor/codemirror.css">
<link rel="stylesheet" href="/workflow/static/vendor/show-hint.css">
<link rel="stylesheet" href="/workflow/static/vendor/lint.css">
<link rel="stylesheet" href="/workflow/static/vendor/schema-editor.css">  <!-- events, states -->
<link rel="stylesheet" href="/workflow/static/urban-workflow.css">

<div id="texte"></div>
<div id="schema"></div>
<span id="etat"></span>

<script src="/workflow/static/vendor/codemirror.js"></script>
<script src="/workflow/static/vendor/simple.js"></script>
<script src="/workflow/static/vendor/show-hint.js"></script>
<script src="/workflow/static/vendor/lint.js"></script>
<script src="/workflow/static/vendor/x6.min.js"></script>          <!-- diagram -->
<script src="/workflow/static/vendor/schema-editor.js"></script>   <!-- events, states -->
<script src="/workflow/static/urban-workflow.js"></script>
<script>
  const ws = UrbanWorkflow.createWorkspace({
    storage: false,                      // the application provides the data
    script: monWorkflow,
    schemas: [{name: "schema_Demande", yaml: "type: object\n…"}],
  });
  UrbanWorkflow.mount("editor", "#texte", {workspace: ws});
  const diagramme = UrbanWorkflow.mount("diagram", "#schema", {workspace: ws});
  diagramme.activate();                  // first display: imports the script
  UrbanWorkflow.mount("status", "#etat", {workspace: ws});

  ws.on("change", (c) => { if (c.what === "script") enregistrer(ws.getScript()); });
</script>
```

Dependencies are only needed for the components that use them: X6 for
`diagram`, the schema editor for `events` and `states`, CodeMirror for
`editor` and `scripts`.

`UrbanWorkflow.mount(name, element | selector, options)` returns the
component instance. All instances have `activate()` (to call when the
component becomes visible again after being hidden: CodeMirror and X6
re-measure, the diagram imports the script on its first display) and
`destroy()`. Some have more:

| Component | Methods |
|---|---|
| `editor` | `codemirror`, `focus()`, `refresh()`; option `readOnly` |
| `diagram` | `reload()`, `generate()`, `getModel()`, `getPositions()`, `setLayoutStore(store)`; option `layoutStore` |
| `simulation` | `run()` (promise of the result) |
| `scripts` | `select(name)`, `runPreview()`, `editor()` |
| `events`, `states` | `select(name)` |
| `tabs` | `show(index)`, `current()`, `component(name)` |

Several instances of the same component can coexist in a page, on the
same workspace or on different ones: no component uses a fixed `id`.

### The workspace

```js
const ws = UrbanWorkflow.createWorkspace({
  apiBase: "https://exemple.fr/workflow/",  // default: derived from the URL of urban-workflow.js
  storage: "local",                       // default; false = nothing is kept;
                                          // or {load(nom), save(nom, valeur)}
  storageKey: "uw-playground",            // prefix of the localStorage keys
  script: "", rules: [], schemas: [], scripts: [], events: [],
  analyzeDelay: 450,                      // ms between a change and the analysis
});
```

| Data | Read | Write |
|---|---|---|
| workflow script | `getScript()` | `setScript(text)`, `insertText(index, text)` |
| simulated rules `{name, params: [{name, type}], result}` | `getRules()` | `setRules(list)`, `setRule(rule)`, `removeRule(name)` |
| schemas `{name, yaml}` | `getSchemas()`, `findSchema(name)` | `setSchemas(list)`, `setSchema(name, yaml)`, `removeSchema(name)` |
| scripts `{name, language, source}` | `getScripts()`, `findScript(name)` | `setScripts(list)`, `setScriptSource(name, source, language)`, `removeScript(name)` |
| sample events | `getEvents()` | `setEvents(list)` |
| last analysis | `getAnalysis()`, `getErrors()`, `getSymbols()` | `analyze()` (immediate, promise) |

Any change to the script, rules, schemas or scripts triggers a new
analysis after `analyzeDelay`. Rules, schemas and scripts are persisted by
`storage`; the script and the events are not (it is up to the application
to keep the workflow wherever it stores it).

Events (`ws.on(name, fn)` returns the unsubscribe function):

| Event | Detail |
|---|---|
| `change` | `{what: "script" \| "rules" \| "schemas" \| "scripts" \| "events", origin}` |
| `analyze` | the new analysis `{ok, errors, symbols, summary}` |
| `analyze-error` | the server did not respond |
| `reveal` | `{component, detail}`: display request (see below) |

Other methods: `simulate(events?)` (promise of the `/api/simulate`
result), `loadExample(example)`, `api(path, body?, method?)` (raw API
call), `payload()` (the common request body).

**Display requests.** A component does not know where the others are.
When it needs to show one (click on an error located in a script,
« Générer le DSL » producing a new text), it calls
`ws.reveal("scripts", {script, line, column})` or `ws.reveal("editor")`.
The target component reacts to the detail, and the `tabs` container
activates the tab that holds it. An application that lays out the
components differently listens to `ws.on("reveal", …)` to do the same.

### Tabs

```js
const onglets = UrbanWorkflow.mount("tabs", "#zone", {
  workspace: ws,
  tabs: [
    {label: "Texte", component: "editor"},
    {label: "Diagramme", component: "diagram", options: {layoutStore: monStockage}},
    {label: "Paramétrage", components: ["rules", "schemas"]},
  ],
  active: 0,                  // index, or name of a component
  onChange: (index, onglet) => {},
});
onglets.component("diagram").reload();
```

The playground page is nothing more than a composition of this kind
(`static/page.js`).

### Appearance

Styles are scoped under the `.uw` class (set by `mount` on each element)
and do not leak into the host page. Colors are CSS variables you can
redefine: `--uw-bg`, `--uw-panel`, `--uw-border`, `--uw-text`,
`--uw-muted`, `--uw-accent`, `--uw-ok`, `--uw-ko`, `--uw-mono`.

```css
:root { --uw-accent: #e0a030; }
```

## The server in a client application

`create_app` builds the FastAPI application (API, page and static files).
Mount it under the prefix of your choice:

```python
from fastapi import FastAPI
from urban_workflow_playground.app import create_app

from mon_appli.regles import plafond_ok, client_connu

app = FastAPI()
app.mount("/workflow", create_app(
    python_functions={"plafond_ok": plafond_ok, "client_connu": client_connu},
    layout_dir="/var/lib/mon-appli/layouts",
))
```

- `python_functions`: `(ctx, **params)` functions that workflows reference
  with `DEFINE RULE … AS @name`; their names are reserved, and the
  `scripts` component shows them read-only. Defaults to the playground
  examples; `{}` to publish none. The browser, for its part, can only
  write `expression` and `jslt` scripts: no Python code coming from the
  browser is ever executed;
- `layout_dir`: directory of the diagram layout files (defaults to
  `PLAYGROUND_LAYOUT_DIR`; otherwise positions stay in the browser).

The page and the components only use **relative** URLs: mounted under
`/workflow`, the playground opens at `/workflow/` (with the trailing
slash) and components loaded from `/workflow/static/…` talk to
`/workflow/api/…` without configuration. A host page served elsewhere
passes `apiBase` to `createWorkspace`.

### HTTP API

| Route | Purpose |
|---|---|
| `POST /api/analyze` | `{script, rules, schemas, scripts}` → `{ok, is_fragment, errors, symbols, summary}`; positioned errors (`line`, `column`, `script` if the error is inside a script) |
| `POST /api/simulate` | same + `events` → steps (impacted workflows, states, actions and messages, log) and final storage state |
| `POST /api/diagram` | `{script}` → surface model of the diagram |
| `POST /api/generate` | `{model, rules, schemas, scripts}` → canonical script + analysis |
| `POST /api/artifact-preview` | `{script, …, artifact, event, state}` → JSON produced by the artifact, or the violations of its schema |
| `GET /api/base-event-schema`, `GET /api/base-state-schema` | common bases (JSON Schema) |
| `GET`/`PUT /api/layout/{workflow}` | diagram layout (below) |
| `GET /healthz` | liveness probe |
| `GET /static/urban-workflow.js`, `/static/urban-workflow.css` | components and styles in one file |

## Diagram layout

Like schemas and scripts, state positions are **not** in the workflow
document: they live in a file next to it, `<workflow>.layout.json`,
indexed by state name:

```json
{"version": 1, "workflow": "Reclamation",
 "states": {"Ouvert": {"x": 280, "y": 60}, "Clos": {"x": 600, "y": 100}}}
```

A state missing from the file (added in the text editor, for example) is
placed automatically, **on its own**: the others keep their place.
« Réorganiser » (Rearrange) repositions everything.

Three ways to store it:

- **files on the server** — with `layout_dir` (or
  `PLAYGROUND_LAYOUT_DIR=/path`), the server reads and writes
  `/path/<workflow>.layout.json` through `GET /api/layout/{workflow}`
  (`{"enabled": true, "layout": …|null}`) and `PUT /api/layout/{workflow}`
  (the document above, or the short form `{"State": {"x": …, "y": …}}`).
  Workflow name and positions are validated, writes are atomic.
  `urban_workflow_playground.layout.LayoutDirectory` does the same from
  Python;
- **browser** — without a directory (`enabled: false`), positions stay in
  `localStorage`;
- **application storage** — the application plugs its own into the
  component:

  ```js
  const diagramme = UrbanWorkflow.mount("diagram", "#schema", {
    workspace: ws,
    layoutStore: {
      load: (workflow) => fetch(`/mon-api/${workflow}/layout`).then(r => r.json()),
      save: (workflow, positions) => fetch(`/mon-api/${workflow}/layout`,
        {method: "PUT", body: JSON.stringify(positions)}),
    },
  });
  // or later: diagramme.setLayoutStore(store); diagramme.reload();
  ```

  `load` returns `{State: {x, y}}` (or a promise, or `null`);
  `setLayoutStore(null)` reverts to the default storage.

## Notes

- A **development** tool: the server has no authentication. An
  application that mounts it puts it behind its own; do not expose it
  publicly as is.
- Simulated rules return the configured boolean (the engine and the
  validation are real; only the internal logic of the rules is replaced).
- The visitor stops at the first semantic error: errors are therefore
  fixed one at a time (syntax errors, however, are reported all at once).
- The diagram works on the script's **surface model**
  (`urban_workflow.dsl.surface`): guards and execution blocks remain raw
  DSL text there; generation rewrites the script in canonical form (`--`
  comments are not preserved). `FRAGMENT` scripts or scripts with
  `INCLUDE` cannot be represented as a diagram.
- `urban_workflow_playground/static/vendor/`: CodeMirror 5.65.18 and AntV
  X6 3.1.8 (MIT licenses), bundled to work offline; the `schema-editor.js`
  schema editor is built from `playground/schema-editor/`.
