# urban-workflow-playground

Site web local pour écrire et tester des scripts de workflow
[urban-workflow](https://pypi.org/project/urban-workflow/) :

- **éditeur** avec coloration du DSL et **intellisense contextuelle**
  (`Ctrl+Espace` ou automatique) : événements après `ON EVENT`, états
  après `SWITCH`, règles après `WHEN`/`AND`/`OR`/`NOT`, actions après
  `EXECUTE`, chemins après `@`, constantes après `=` — alimentée en
  continu par l'analyse **réelle** du script (parseur ANTLR + visiteur) ;
- **diagnostics positionnés** (syntaxe et validation sémantique),
  soulignés dans l'éditeur et cliquables ;
- **paramétrage** : déclaration des règles métier disponibles (nom,
  paramètres typés, résultat simulé), persistée dans le navigateur —
  c'est contre ces signatures que les appels `WHEN` sont validés ;
- **structure** : vue arborescente de la configuration compilée
  (initialiseurs, états, transitions) ;
- **simulation** : une liste JSON d'événements rejoués dans l'ordre sur
  le vrai moteur en mémoire — états atteints, actions poussées
  (messages inclus), journal fonctionnel des règles ;
- **diagramme** : vue graphique du workflow (états, transitions,
  initialiseurs ⚡, expirations ⏰). « Importer le DSL » reconstruit le
  diagramme depuis l'éditeur ; on déplace les états, « Relier » trace
  une transition en glissant d'un état (ou de ⚡) vers un état, le clic
  ouvre les propriétés (événement, garde `WHEN`, blocs
  `EXECUTE`/`STORE`, cible `SWITCH`, priorité des branches) ;
  « Générer le DSL → éditeur » rend le script **canonique** et le
  valide par l'analyse réelle. Les positions sont enregistrées hors du
  script (voir « Mise en page du diagramme »).

## Lancement

```bash
pip install urban-workflow-playground
urban-workflow-playground            # http://127.0.0.1:8777
```

ou `python -m urban_workflow_playground`. Variables : `PLAYGROUND_HOST`
(défaut `127.0.0.1`), `PLAYGROUND_PORT` (défaut `8777`),
`PLAYGROUND_LAYOUT_DIR` (répertoire des mises en page, voir ci-dessous).

Depuis un clone du dépôt : `pip install -e ./playground`.

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

- **fichiers sur le serveur** — avec `PLAYGROUND_LAYOUT_DIR=/chemin`, le
  playground lit et écrit `/chemin/<workflow>.layout.json` via
  `GET /api/layout/{workflow}` (`{"enabled": true, "layout": …|null}`) et
  `PUT /api/layout/{workflow}` (le document ci-dessus, ou la forme courte
  `{"Etat": {"x": …, "y": …}}`). Nom de workflow et positions contrôlés,
  écriture atomique. `urban_workflow_playground.layout.LayoutDirectory`
  fait la même chose depuis Python ;
- **navigateur** — sans `PLAYGROUND_LAYOUT_DIR` (`enabled: false`), les
  positions restent dans le `localStorage` ;
- **stockage de l'application** — une application qui intègre le
  diagramme branche le sien :

  ```js
  PlaygroundDiagram.setLayoutStore({
    load: (workflow) => fetch(`/mon-api/${workflow}/layout`).then(r => r.json()),
    save: (workflow, positions) => fetch(`/mon-api/${workflow}/layout`,
      {method: "PUT", body: JSON.stringify(positions)}),
  });
  PlaygroundDiagram.reload();   // relit les positions avec ce stockage
  ```

  `load` rend `{Etat: {x, y}}` (ou une promesse, ou `null`) ;
  `setLayoutStore(null)` revient au stockage par défaut.

## Notes

- Outil de **développement local** : aucune authentification, ne pas
  exposer publiquement.
- Les règles simulées retournent le booléen configuré (le moteur et la
  validation sont réels ; seule la logique interne des règles est
  remplacée).
- Le visiteur s'arrête à la première erreur sémantique : les erreurs
  se corrigent donc une par une (la syntaxe, elle, est remontée en bloc).
- La vue diagramme travaille sur le **modèle de surface** du script
  (`urban_workflow.dsl.surface`) : gardes et blocs d'exécution y restent
  du texte DSL brut ; la génération réécrit le script en forme
  canonique (commentaires `--` non conservés). Les scripts `FRAGMENT`
  ou à `INCLUDE` ne sont pas représentables en diagramme.
- `urban_workflow_playground/static/vendor/` : CodeMirror 5.65.18 et
  AntV X6 3.1.8 (licences MIT), embarqués pour fonctionner hors ligne.
