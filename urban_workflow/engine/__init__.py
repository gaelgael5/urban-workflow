"""Moteur d'exécution : factory, processor, engine et chaîne d'append.

Portage de ``WorkflowEngine`` / ``WorkflowProcessor`` / ``WorkflowFactory``
et de la chaîne de responsabilité ``AppendEvents``. La traduction des
actions collectées en messages (``TranslateActions``) passe par la couture
:class:`ActionTranslator` — l'étape 4 y branchera les templates urban-json.
"""

from .append_events import (
    AppendEventResponsibility,
    AppendResultActionEvent,
    AppendStandardEvent,
)
from .engine import WorkflowEngine
from .factory import WorkflowFactory
from .processor import WorkflowProcessor
from .serializer import parse_incoming_event, populate_incoming_event
from .translator import ActionTranslator, DefaultActionTranslator

__all__ = [
    "ActionTranslator",
    "AppendEventResponsibility",
    "AppendResultActionEvent",
    "AppendStandardEvent",
    "DefaultActionTranslator",
    "WorkflowEngine",
    "WorkflowFactory",
    "WorkflowProcessor",
    "parse_incoming_event",
    "populate_incoming_event",
]
