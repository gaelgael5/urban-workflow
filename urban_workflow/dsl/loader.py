"""Chargement de répertoires de scripts DSL (portage de ``WorkflowsConfigLoader``).

Les scripts ``FRAGMENT`` sont indexés par nom de fichier ; chaque script
complet est visité par un visiteur neuf, précédé de la visite de ses
``INCLUDE`` (qui alimentent déclarations, constantes et événements).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..config import WorkflowsConfig
from .parser import WorkflowScriptParser
from .visitor import WorkflowConfigVisitor

VisitorFactory = Callable[[], WorkflowConfigVisitor]


def parse_directory(
    path: str | Path, pattern: str = "*"
) -> list[WorkflowScriptParser]:
    """Analyse tous les fichiers de ``path`` correspondant à ``pattern``."""
    directory = Path(path)
    return [
        WorkflowScriptParser.parse_path(item)
        for item in sorted(directory.glob(pattern))
        if item.is_file()
    ]


def load_directory(
    config: WorkflowsConfig,
    visitor_factory: VisitorFactory,
    path: str | Path,
    pattern: str = "*",
) -> WorkflowsConfig:
    """Charge dans ``config`` tous les workflows d'un répertoire.

    ``visitor_factory`` fabrique un :class:`WorkflowConfigVisitor` neuf par
    script complet (avec ses règles métier déjà enregistrées).
    """
    parsers = parse_directory(path, pattern)
    for parser in parsers:
        parser.check()

    fragments: dict[str, WorkflowScriptParser] = {}
    for parser in parsers:
        if parser.is_fragment:
            fragments[parser.filename] = parser
            fragments[Path(parser.filename).name] = parser

    for parser in parsers:
        if parser.is_fragment:
            continue

        visitor = visitor_factory()

        for include in parser.includes:
            fragment = fragments.get(include) or fragments.get(Path(include).name)
            if fragment is None:
                raise FileNotFoundError(f"missing file {include}")
            fragment.visit(visitor)

        document = parser.visit(visitor)
        config.add_document(document)

    return config
