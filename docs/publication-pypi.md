# Publication PyPI

Deux distributions sont publiées depuis ce dépôt, par **trusted
publishing** (OIDC) — aucun token stocké nulle part :

| Distribution | Source | Tag déclencheur |
|---|---|---|
| `urban-workflow` | racine du dépôt | `vX.Y.Z` |
| `urban-workflow-playground` | `playground/` | `playground-vX.Y.Z` |

Le workflow [`release.yml`](../.github/workflows/release.yml) construit
(sdist + wheel), vérifie que le tag correspond à la version du
`pyproject.toml`, et publie.

## Mise en place (une seule fois, par le propriétaire du compte PyPI)

1. Se connecter sur [pypi.org](https://pypi.org) (compte qui possède
   déjà `urban-json`).
2. *Your account → Publishing → Add a new pending publisher*, **deux
   fois** (une par projet), avec exactement :

   | Champ | Valeur |
   |---|---|
   | PyPI Project Name | `urban-workflow` puis `urban-workflow-playground` |
   | Owner | `gaelgael5` |
   | Repository name | `urban-workflow` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

3. (Recommandé) Sur GitHub : *Settings → Environments → New
   environment* nommé `pypi` — optionnellement avec des *required
   reviewers* pour approuver chaque publication.

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
