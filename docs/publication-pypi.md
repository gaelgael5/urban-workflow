# Publication PyPI

Deux distributions sont publiées depuis ce dépôt, chacune par **son
propre workflow** et son propre environment, via *trusted publishing*
(OIDC) — aucun token stocké nulle part :

| Distribution | Source | Workflow | Environment | Tag déclencheur |
|---|---|---|---|---|
| `urban-workflow` | racine | `release-core.yml` | `pypi` | `vX.Y.Z` |
| `urban-workflow-playground` | `playground/` | `release-playground.yml` | `pypi-playground` | `playground-vX.Y.Z` |

Chaque workflow construit (sdist + wheel), vérifie que le tag correspond
à la version du `pyproject.toml` concerné, et publie. Un workflow par
paquet : chaque projet PyPI ne fait confiance qu'au workflow qui le
publie.

## Mise en place (une seule fois, par le propriétaire du compte PyPI)

1. Se connecter sur [pypi.org](https://pypi.org) (compte qui possède
   déjà `urban-json`).
2. *Your account → Publishing → Add a new pending publisher*, **deux
   fois** :

   | Champ | Publisher 1 | Publisher 2 |
   |---|---|---|
   | PyPI Project Name | `urban-workflow` | `urban-workflow-playground` |
   | Owner | `gaelgael5` | `gaelgael5` |
   | Repository name | `urban-workflow` | `urban-workflow` |
   | Workflow name | `release-core.yml` | `release-playground.yml` |
   | Environment name | `pypi` | `pypi-playground` |

3. (Recommandé) Sur GitHub : *Settings → Environments* — créer `pypi`
   et `pypi-playground`, optionnellement avec des *required reviewers*
   pour approuver chaque publication.

## Publier une version

```bash
# 1. S'assurer que la version du pyproject.toml concerné est la bonne.
# 2. Tagger et pousser :
git tag v0.1.0 && git push origin v0.1.0
```

```bash
git tag playground-v0.1.0 && git push origin playground-v0.1.0
```

Le job refuse de publier si le tag ne correspond pas à la version
déclarée. Pour une nouvelle version : bump de `version` dans le
`pyproject.toml` concerné, commit, nouveau tag.

## Vérification locale avant tag

```bash
python -m pip install build twine
python -m build . && python -m build playground/
python -m twine check dist/* playground/dist/*
```
