"""Les pages PyPI des deux paquets.

pypi.org affiche le ``readme`` déclaré dans chaque pyproject : il doit être
en anglais (décision du 2026-11-08 : la 0.2.0 est partie avec les README
français) et ne contenir que des liens absolus — un lien relatif
(``docs/guide-dsl.md``) pointe dans le vide depuis pypi.org.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = [ROOT, ROOT / "playground"]

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    tomllib = pytest.importorskip("tomli")


def _readme(project: Path) -> Path:
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    return project / data["project"]["readme"]


@pytest.mark.parametrize("project", PROJECTS, ids=["urban-workflow", "playground"])
def test_pypi_readme_is_the_english_one(project):
    readme = _readme(project)
    assert readme.name == "README.en.md"
    assert readme.read_text(encoding="utf-8").splitlines()[2].startswith("*English")


@pytest.mark.parametrize("project", PROJECTS, ids=["urban-workflow", "playground"])
def test_pypi_readme_has_only_absolute_links(project):
    text = _readme(project).read_text(encoding="utf-8")
    # Les blocs de code ne sont pas des liens.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    targets = re.findall(r"\]\(([^)\s]+)", text)
    assert targets, "la page doit renvoyer vers la documentation"
    relative = [t for t in targets if not re.match(r"(https?://|mailto:|#)", t)]
    assert relative == []


@pytest.mark.parametrize("project", PROJECTS, ids=["urban-workflow", "playground"])
def test_pypi_readme_links_point_at_the_declared_version(project):
    """Les liens doivent viser le tag de CETTE version.

    Sinon la page annonce une documentation que le tag visé ne contient
    pas : la 0.3.0 vantait les clés de dédoublonnage en renvoyant au tag
    v0.2.1, où la section n'existait pas.
    """
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    version = data["project"]["version"]
    text = _readme(project).read_text(encoding="utf-8")

    tags = set(re.findall(r"/blob/(v[^/]+)/", text))
    assert tags, "la page doit renvoyer vers un tag du dépôt"
    assert tags == {f"v{version}"}, (
        f"liens vers {sorted(tags)} alors que la version déclarée est {version}"
    )


@pytest.mark.parametrize("project", PROJECTS, ids=["urban-workflow", "playground"])
def test_pypi_summary_is_english(project):
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    summary = data["project"]["description"]
    assert not re.search(r"[éèàù]| piloté | moteur ", summary), summary
