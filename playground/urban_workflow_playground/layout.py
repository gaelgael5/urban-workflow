"""Mise en page du diagramme : un fichier ``<workflow>.layout.json`` par workflow.

Décision utilisateur du 2026-11-07 : comme les schémas et les scripts, la
mise en page reste HORS du document de workflow (le DSL ne porte que la
sémantique). Elle vit dans un fichier à côté, dont le format est
volontairement minimal pour qu'une application l'écrive elle-même :

.. code-block:: json

    {"version": 1, "workflow": "Reclamation",
     "states": {"Ouvert": {"x": 280, "y": 60}, "Clos": {"x": 600, "y": 100}}}

Les positions sont indexées par NOM d'état : un état absent du fichier est
placé automatiquement par le diagramme (lui seul, les autres gardent leur
place).

:class:`LayoutDirectory` lit et écrit ces fichiers dans un répertoire —
c'est ce qu'utilisent les routes ``/api/layout/{workflow}`` du playground
quand ``PLAYGROUND_LAYOUT_DIR`` est défini.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

LAYOUT_VERSION = 1
LAYOUT_SUFFIX = ".layout.json"

# Le nom du workflow devient un nom de fichier : on n'accepte que ce que le
# DSL accepte comme clé (identifiant, points de nom composé), ce qui exclut
# d'emblée « / », « .. » en tête et tout caractère de chemin.
_WORKFLOW_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_$#.\-]{0,127}$")
# Garde-fou contre un fichier démesuré envoyé à l'API (un workflow réel
# compte quelques dizaines d'états).
MAX_STATES = 2000


class LayoutError(ValueError):
    """Mise en page invalide (nom de workflow ou contenu)."""


def check_workflow_name(name: str) -> str:
    if not _WORKFLOW_NAME.match(name or "") or ".." in name:
        raise LayoutError(f"invalid workflow name for a layout file: {name!r}")
    return name


def normalize_layout(data: Any, workflow: str) -> dict[str, Any]:
    """Valide un document de mise en page et le remet sous forme canonique.

    Accepte aussi la forme courte ``{"Etat": {"x": …, "y": …}}`` (ce que
    le diagramme manipule) pour qu'une application n'ait pas à envelopper.
    """
    if not isinstance(data, dict):
        raise LayoutError("layout must be a JSON object")
    states = data["states"] if "states" in data else data
    if not isinstance(states, dict):
        raise LayoutError("'states' must be an object")
    if len(states) > MAX_STATES:
        raise LayoutError(f"too many states in layout (max {MAX_STATES})")
    clean: dict[str, dict[str, float]] = {}
    for name, pos in states.items():
        if not isinstance(name, str) or not name:
            raise LayoutError("state names must be non-empty strings")
        if not isinstance(pos, dict):
            raise LayoutError(f"position of state {name!r} must be an object")
        coords = {}
        for axis in ("x", "y"):
            value = pos.get(axis)
            # bool est un int en Python : on l'écarte explicitement.
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(value):
                raise LayoutError(f"state {name!r}: '{axis}' must be a finite number")
            coords[axis] = value
        clean[name] = coords
    return {"version": LAYOUT_VERSION, "workflow": workflow, "states": clean}


class LayoutDirectory:
    """Fichiers ``<workflow>.layout.json`` d'un répertoire."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def file_for(self, workflow: str) -> Path:
        return self.path / (check_workflow_name(workflow) + LAYOUT_SUFFIX)

    def load(self, workflow: str) -> dict[str, Any] | None:
        """Mise en page du workflow, ``None`` s'il n'y en a pas encore."""
        file = self.file_for(workflow)
        if not file.is_file():
            return None
        return normalize_layout(json.loads(file.read_text(encoding="utf-8")), workflow)

    def save(self, workflow: str, data: Any) -> dict[str, Any]:
        layout = normalize_layout(data, workflow)
        file = self.file_for(workflow)
        self.path.mkdir(parents=True, exist_ok=True)
        # Écriture atomique (fichier temporaire + rename) : un enregistrement
        # interrompu ne laisse jamais un JSON tronqué que load() refuserait.
        fd, tmp = tempfile.mkstemp(dir=self.path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(layout, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            # mkstemp crée en 0600 : une mise en page n'est pas un secret, et
            # le fichier doit rester lisible par l'application qui le relit.
            os.chmod(tmp, 0o644)
            os.replace(tmp, file)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return layout
