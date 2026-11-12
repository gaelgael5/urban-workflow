"""DSL de déclaration des workflows.

Grammaires ANTLR reprises telles quelles du projet source
(``urban_workflow/dsl/grammar/``), parseur Python généré
(``urban_workflow/dsl/generated/``, ANTLR 4.13.2), visiteur de construction
:class:`WorkflowConfigVisitor` et chargeur de répertoires avec
``INCLUDE``/``FRAGMENT``.

Point d'entrée simple ::

    from urban_workflow import FunctionRegistry
    from urban_workflow.dsl import parse_config

    rules = FunctionRegistry("rule")
    rules.add("IsMajor", is_major)
    config = parse_config(script_text, rules=rules, filename="demo.wf")
"""

from __future__ import annotations

from ..config import WorkflowConfig
from ..registry import FunctionRegistry
from .errors import DslErrorModel
from .loader import load_directory, parse_directory
from .parser import WorkflowScriptParser
from .surface import SurfaceError, SurfaceModel, extract_surface, render_script
from .visitor import ConstantModel, DeclaredFunction, WorkflowConfigVisitor

__all__ = [
    "ConstantModel",
    "DeclaredFunction",
    "DslErrorModel",
    "SurfaceError",
    "SurfaceModel",
    "WorkflowConfigVisitor",
    "WorkflowScriptParser",
    "extract_surface",
    "load_directory",
    "parse_config",
    "parse_directory",
    "render_script",
]


def parse_config(
    source: str,
    rules: FunctionRegistry | None = None,
    filename: str = "",
    schemas=None,
    scripts=None,
) -> WorkflowConfig:
    """Analyse un script DSL complet et construit sa configuration.

    Lève :class:`~urban_workflow.exceptions.DslSyntaxError` sur erreur de
    syntaxe, et les exceptions de validation positionnées du visiteur sur
    erreur sémantique (règle non enregistrée, action non déclarée,
    argument inconnu ou manquant, état ``SWITCH`` absent…).
    """
    parser = WorkflowScriptParser.parse_string(source, filename=filename).check()
    visitor = WorkflowConfigVisitor(
        rules=rules, filename=filename, schemas=schemas, scripts=scripts
    )
    return parser.visit(visitor)
