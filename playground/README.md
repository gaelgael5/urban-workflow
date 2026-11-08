# urban-workflow-playground

Composants web pour écrire, visualiser et tester des workflows
[urban-workflow](https://pypi.org/project/urban-workflow/), et le serveur
qui leur fournit l'analyse et la simulation **réelles** (parseur ANTLR,
visiteur, moteur en mémoire).

Le paquet sert deux usages :

- **le playground** : une page prête à l'emploi (`urban-workflow-playground`,
  port 8777) qui assemble tous les composants ;
- **une application cliente** : elle monte les composants qu'elle veut, où
  elle veut (l'éditeur seul, le diagramme à côté d'un formulaire, des
  onglets de son choix…), et sert l'API dans sa propre application FastAPI.

## Lancement du playground

```bash
pip install urban-workflow-playground
urban-workflow-playground            # http://127.0.0.1:8777
```

ou `python -m urban_workflow_playground`. Variables : `PLAYGROUND_HOST`
(défaut `127.0.0.1`), `PLAYGROUND_PORT` (défaut `8777`),
`PLAYGROUND_LAYOUT_DIR` (répertoire des mises en page, voir plus bas).

Depuis un clone du dépôt : `pip install -e ./playground`.

## Les composants

Chaque composant s'affiche dans l'élément qu'on lui donne et ne
communique avec les autres **que par un espace de travail** partagé. Aucun
n'est obligatoire, aucun ne suppose la présence d'un autre.

| Nom | Ce qu'il affiche |
|---|---|
| `editor` | texte du workflow : coloration, **intellisense contextuelle** (`Ctrl+Espace` ou automatique), erreurs soulignées et listées dessous (option `diagnostics: false` pour ne pas les lister) |
| `status` | badge du résultat de la dernière analyse (« script valide », « 2 erreur(s) ») |
| `diagram` | vue graphique éditable (états, transitions, initialiseurs ⚡, expirations ⏰), avec sa barre d'outils ; « Générer le DSL » réécrit le script canonique dans l'espace |
| `events` | liste des événements ; pour chacun, le socle commun (lecture seule) et l'éditeur visuel de son schéma métier |
| `states` | même chose pour les états |
| `scripts` | scripts des règles (`AS @nom`, langage `expression`) et des artefacts (`USING @nom`, langage `jslt`), avec complétion, erreurs dans le script et aperçu du JSON produit ; fonctions Python du serveur en lecture seule |
| `rules` | règles métier **simulées** (les règles de code n'existent pas dans le navigateur : nom, paramètres typés, résultat) |
| `schemas` | schémas JSON (YAML) des événements, états et artefacts, avec qui les utilise |
| `structure` | configuration compilée : initialiseurs, états, transitions |
| `simulation` | événements JSON rejoués sur le vrai moteur en mémoire : états atteints, actions et leurs messages, journal |
| `help` | aide-mémoire du langage |
| `examples` | liste déroulante des exemples, qui charge l'exemple choisi dans l'espace |
| `tabs` | conteneur à onglets de composants (facultatif) |

`UrbanWorkflow.components()` liste les composants chargés, avec leur
libellé et leur description.

### Monter des composants

Une page hôte charge les dépendances (CodeMirror, X6, l'éditeur de schémas)
puis **un seul fichier** de composants, `static/urban-workflow.js`, et sa
feuille de style :

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
    storage: false,                      // l'application fournit les données
    script: monWorkflow,
    schemas: [{name: "schema_Demande", yaml: "type: object\n…"}],
  });
  UrbanWorkflow.mount("editor", "#texte", {workspace: ws});
  const diagramme = UrbanWorkflow.mount("diagram", "#schema", {workspace: ws});
  diagramme.activate();                  // premier affichage : importe le script
  UrbanWorkflow.mount("status", "#etat", {workspace: ws});

  ws.on("change", (c) => { if (c.what === "script") enregistrer(ws.getScript()); });
</script>
```

Les dépendances ne sont nécessaires que pour les composants qui s'en
servent : X6 pour `diagram`, l'éditeur de schémas pour `events` et
`states`, CodeMirror pour `editor` et `scripts`.

`UrbanWorkflow.mount(nom, élément | sélecteur, options)` retourne
l'instance du composant. Toutes ont `activate()` (à appeler quand le
composant redevient visible après avoir été caché : CodeMirror et X6
remesurent, le diagramme importe le script à son premier affichage) et
`destroy()`. Quelques-unes ont davantage :

| Composant | Méthodes |
|---|---|
| `editor` | `codemirror`, `focus()`, `refresh()` ; option `readOnly` |
| `diagram` | `reload()`, `generate()`, `getModel()`, `getPositions()`, `setLayoutStore(store)` ; option `layoutStore` |
| `simulation` | `run()` (promesse du résultat) |
| `scripts` | `select(nom)`, `runPreview()`, `editor()` |
| `events`, `states` | `select(nom)` |
| `tabs` | `show(index)`, `current()`, `component(nom)` |

Plusieurs instances d'un même composant peuvent coexister dans une page,
sur le même espace de travail ou sur des espaces différents : aucun
composant n'utilise d'`id` fixe.

### L'espace de travail

```js
const ws = UrbanWorkflow.createWorkspace({
  apiBase: "https://exemple.fr/workflow/",  // défaut : déduit de l'URL de urban-workflow.js
  storage: "local",                       // défaut ; false = rien n'est gardé ;
                                          // ou {load(nom), save(nom, valeur)}
  storageKey: "uw-playground",            // préfixe des clés du localStorage
  script: "", rules: [], schemas: [], scripts: [], events: [],
  analyzeDelay: 450,                      // ms entre une modification et l'analyse
});
```

| Donnée | Lire | Écrire |
|---|---|---|
| script du workflow | `getScript()` | `setScript(texte)`, `insertText(index, texte)` |
| règles simulées `{name, params: [{name, type}], result}` | `getRules()` | `setRules(liste)`, `setRule(règle)`, `removeRule(nom)` |
| schémas `{name, yaml}` | `getSchemas()`, `findSchema(nom)` | `setSchemas(liste)`, `setSchema(nom, yaml)`, `removeSchema(nom)` |
| scripts `{name, language, source}` | `getScripts()`, `findScript(nom)` | `setScripts(liste)`, `setScriptSource(nom, source, langage)`, `removeScript(nom)` |
| événements d'exemple | `getEvents()` | `setEvents(liste)` |
| dernière analyse | `getAnalysis()`, `getErrors()`, `getSymbols()` | `analyze()` (immédiate, promesse) |

Toute modification du script, des règles, des schémas ou des scripts
relance l'analyse après `analyzeDelay`. Les règles, schémas et scripts sont
persistés par `storage` ; le script et les événements ne le sont pas
(c'est à l'application de garder le workflow là où elle le range).

Événements (`ws.on(nom, fn)` retourne la fonction de désabonnement) :

| Événement | Détail |
|---|---|
| `change` | `{what: "script" \| "rules" \| "schemas" \| "scripts" \| "events", origin}` |
| `analyze` | la nouvelle analyse `{ok, errors, symbols, summary}` |
| `analyze-error` | le serveur n'a pas répondu |
| `reveal` | `{component, detail}` : demande d'affichage (voir plus bas) |

Autres méthodes : `simulate(events?)` (promesse du résultat de
`/api/simulate`), `loadExample(exemple)`, `api(chemin, corps?, méthode?)`
(appel brut à l'API), `payload()` (le corps commun des requêtes).

**Demandes d'affichage.** Un composant ne sait pas où sont les autres. Quand
il a besoin d'en montrer un (clic sur une erreur située dans un script,
« Générer le DSL » qui produit un nouveau texte), il appelle
`ws.reveal("scripts", {script, line, column})` ou `ws.reveal("editor")`. Le
composant visé réagit au détail, et le conteneur `tabs` active l'onglet qui
le porte. Une application qui range les composants autrement écoute
`ws.on("reveal", …)` pour faire de même.

### Onglets

```js
const onglets = UrbanWorkflow.mount("tabs", "#zone", {
  workspace: ws,
  tabs: [
    {label: "Texte", component: "editor"},
    {label: "Diagramme", component: "diagram", options: {layoutStore: monStockage}},
    {label: "Paramétrage", components: ["rules", "schemas"]},
  ],
  active: 0,                  // index, ou nom d'un composant
  onChange: (index, onglet) => {},
});
onglets.component("diagram").reload();
```

La page du playground n'est qu'une composition de ce genre
(`static/page.js`).

### Apparence

Les styles sont rangés sous la classe `.uw` (posée par `mount` sur chaque
élément) et ne débordent pas sur la page hôte. Les couleurs sont des
variables CSS à redéfinir : `--uw-bg`, `--uw-panel`, `--uw-border`,
`--uw-text`, `--uw-muted`, `--uw-accent`, `--uw-ok`, `--uw-ko`, `--uw-mono`.

```css
:root { --uw-accent: #e0a030; }
```

## Le serveur dans une application cliente

`create_app` fabrique l'application FastAPI (API, page et fichiers
statiques). On la monte sous le préfixe de son choix :

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

- `python_functions` : fonctions `(ctx, **params)` que les workflows
  référencent par `DEFINE RULE … AS @nom` ; leurs noms sont réservés, et
  le composant `scripts` les montre en lecture seule. Par défaut, les
  exemples du playground ; `{}` pour n'en publier aucune. Le navigateur, lui,
  ne peut écrire que des scripts `expression` et `jslt` : aucun code Python
  venu du navigateur n'est exécuté ;
- `layout_dir` : répertoire des fichiers de mise en page du diagramme (par
  défaut `PLAYGROUND_LAYOUT_DIR`, sinon les positions restent dans le
  navigateur).

La page et les composants n'utilisent que des URL **relatives** : monté
sous `/workflow`, le playground s'ouvre sur `/workflow/` (avec la barre
finale) et les composants chargés depuis `/workflow/static/…` parlent à
`/workflow/api/…` sans configuration. Une page hôte servie ailleurs passe
`apiBase` à `createWorkspace`.

### API HTTP

| Route | Rôle |
|---|---|
| `POST /api/analyze` | `{script, rules, schemas, scripts}` → `{ok, is_fragment, errors, symbols, summary}` ; erreurs positionnées (`line`, `column`, `script` si l'erreur est dans un script) |
| `POST /api/simulate` | idem + `events` → étapes (workflows impactés, états, actions et messages, journal) et état final du stockage |
| `POST /api/diagram` | `{script}` → modèle de surface du diagramme |
| `POST /api/generate` | `{model, rules, schemas, scripts}` → script canonique + analyse |
| `POST /api/artifact-preview` | `{script, …, artifact, event, state}` → JSON produit par l'artefact, ou les violations de son schéma |
| `GET /api/base-event-schema`, `GET /api/base-state-schema` | socles communs (JSON Schema) |
| `GET`/`PUT /api/layout/{workflow}` | mise en page du diagramme (ci-dessous) |
| `GET /healthz` | sonde de vie |
| `GET /static/urban-workflow.js`, `/static/urban-workflow.css` | composants et styles en un fichier |

## Mise en page du diagramme

Comme les schémas et les scripts, la position des états n'est **pas** dans
le document de workflow : elle vit dans un fichier à côté,
`<workflow>.layout.json`, indexé par nom d'état :

```json
{"version": 1, "workflow": "Reclamation",
 "states": {"Ouvert": {"x": 280, "y": 60}, "Clos": {"x": 600, "y": 100}}}
```

Un état absent du fichier (ajouté dans l'éditeur de texte, par exemple) est
placé automatiquement, **seul** : les autres gardent leur place.
« Réorganiser » replace tout.

Trois manières de l'enregistrer :

- **fichiers sur le serveur** — avec `layout_dir` (ou
  `PLAYGROUND_LAYOUT_DIR=/chemin`), le serveur lit et écrit
  `/chemin/<workflow>.layout.json` via `GET /api/layout/{workflow}`
  (`{"enabled": true, "layout": …|null}`) et `PUT /api/layout/{workflow}`
  (le document ci-dessus, ou la forme courte `{"Etat": {"x": …, "y": …}}`).
  Nom de workflow et positions contrôlés, écriture atomique.
  `urban_workflow_playground.layout.LayoutDirectory` fait la même chose
  depuis Python ;
- **navigateur** — sans répertoire (`enabled: false`), les positions
  restent dans le `localStorage` ;
- **stockage de l'application** — elle branche le sien sur le composant :

  ```js
  const diagramme = UrbanWorkflow.mount("diagram", "#schema", {
    workspace: ws,
    layoutStore: {
      load: (workflow) => fetch(`/mon-api/${workflow}/layout`).then(r => r.json()),
      save: (workflow, positions) => fetch(`/mon-api/${workflow}/layout`,
        {method: "PUT", body: JSON.stringify(positions)}),
    },
  });
  // ou plus tard : diagramme.setLayoutStore(store); diagramme.reload();
  ```

  `load` rend `{Etat: {x, y}}` (ou une promesse, ou `null`) ;
  `setLayoutStore(null)` revient au stockage par défaut.

## Notes

- Outil de **développement** : le serveur n'a aucune authentification.
  Une application qui le monte le place derrière la sienne ; ne pas
  l'exposer publiquement tel quel.
- Les règles simulées retournent le booléen configuré (le moteur et la
  validation sont réels ; seule la logique interne des règles est
  remplacée).
- Le visiteur s'arrête à la première erreur sémantique : les erreurs se
  corrigent donc une par une (la syntaxe, elle, est remontée en bloc).
- Le diagramme travaille sur le **modèle de surface** du script
  (`urban_workflow.dsl.surface`) : gardes et blocs d'exécution y restent du
  texte DSL brut ; la génération réécrit le script en forme canonique
  (commentaires `--` non conservés). Les scripts `FRAGMENT` ou à `INCLUDE`
  ne sont pas représentables en diagramme.
- `urban_workflow_playground/static/vendor/` : CodeMirror 5.65.18 et AntV X6
  3.1.8 (licences MIT), embarqués pour fonctionner hors ligne ; éditeur de
  schémas `schema-editor.js` construit depuis `playground/schema-editor/`.
