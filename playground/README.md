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
  valide par l'analyse réelle. Les positions sont mémorisées dans le
  navigateur par nom de workflow.

## Lancement

```bash
pip install urban-workflow-playground
urban-workflow-playground            # http://127.0.0.1:8777
```

ou `python -m urban_workflow_playground`. Variables : `PLAYGROUND_HOST`
(défaut `127.0.0.1`), `PLAYGROUND_PORT` (défaut `8777`).

Depuis un clone du dépôt : `pip install -e ./playground`.

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
