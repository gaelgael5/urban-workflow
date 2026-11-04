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
  (messages inclus), journal fonctionnel des règles.

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
- `urban_workflow_playground/static/vendor/` : CodeMirror 5.65.18
  (licence MIT), embarqué pour fonctionner hors ligne.
