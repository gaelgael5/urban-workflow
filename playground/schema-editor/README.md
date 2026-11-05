# Éditeur visuel de schémas (bundle navigateur)

Construit `urban_workflow_playground/static/vendor/schema-editor.js` (+ `.css`),
utilisé par la vue **Événements** du playground pour éditer la structure des
événements.

- **Composant** : `SchemaFieldsEditor` de [jsonjoy-builder](https://github.com/lovasoa/jsonjoy-builder)
  (licence MIT), le **même** que l'éditeur de modèles du portail Miles
  (`portail/frontend/src/dataModels/SchemaEditor.tsx`).
- **Paquet vendu** `vendor/jsonjoy-builder-1.0.4-89529b6.tgz` : copie à
  l'identique de celui de Miles (`portail/frontend/vendor/`, sha256
  `869e31315b699f0e…`). La version npm 1.0.4 ne gère pas les `$ref` ; ce fork
  est construit depuis le commit `89529b6` (2 septembre 2026). Voir la
  provenance détaillée dans le README du dossier vendor de Miles ; repasser
  sur npm dès qu'une version ≥ 1.0.5 publie ce support, **dans les deux
  dépôts à la fois**.
- **API exposée** : `window.UWSchemaEditor.mount(el, {value, onChange,
  readOnly})` → `{update, unmount}` ; `parseYaml(text)` → `{value}` ou
  `{error}` ; `stringifyYaml(obj)`.

## Reconstruire

```bash
cd playground/schema-editor
npm ci
npm run build
```

Le bundle est commité : ni l'image Docker ni la distribution PyPI n'ont
besoin de Node.
