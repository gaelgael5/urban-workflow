"""Traduction des actions collectées en actions matérialisées.

C'est la couture correspondant à ``WorkflowProcessor.TranslateActions`` du
source (templates + métadonnées → ``MessageRaw`` → ``PushedAction``).
L'étape 4 branchera ici le ``TemplateRegistry`` urban-json ;
:class:`DefaultActionTranslator` fournit en attendant une matérialisation
JSON-compatible sans template, y compris l'encapsulation ``$_reminder``
des actions différées.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .. import constants
from ..clock import WorkflowClock
from ..models import ChangeEnum, PushedAction, ResultAction, RunContext


class ActionTranslator(ABC):
    """Traduit une :class:`ResultAction` en :class:`PushedAction`."""

    @abstractmethod
    def translate(self, ctx: RunContext, action: ResultAction) -> PushedAction: ...


class DefaultActionTranslator(ActionTranslator):
    """Matérialisation par défaut, sans template.

    Le corps du message reprend la forme du template par défaut du source
    (``TemplateModels.DefaultAction``) : identité de l'action, arguments
    résolus contre le contexte, identité du workflow et de l'événement.
    Le message produit a la forme ``MessageRaw`` du source
    (``{"Header": {...}, "Body": {...}}``), la même que celle du
    ``JsltActionTranslator`` de :mod:`urban_workflow.templating`.
    """

    def translate(self, ctx: RunContext, action: ResultAction) -> PushedAction:
        body = self.build_body(ctx, action)

        if action.delay > 0:
            body = self.wrap_reminder(action, body)

        return PushedAction(
            uuid=action.uuid,
            name=action.name,
            kind=action.kind,
            change=ChangeEnum.NEW,
            execute_message={"Header": {}, "Body": body},
        )

    def build_body(self, ctx: RunContext, action: ResultAction) -> dict[str, Any]:
        event = action.event
        return {
            "Uuid": str(action.uuid),
            "Name": action.name,
            "Kind": action.kind,
            "PushedAt": WorkflowClock.now().isoformat(),
            "Arguments": action.resolve_arguments(ctx),
            "WorkflowId": str(ctx.workflow.uuid),
            "ExternalId": ctx.workflow.external_id,
            "EventId": str(event.uuid) if event is not None else None,
            "FromState": event.from_state if event is not None else "",
            "ToState": event.to_state if event is not None else "",
        }

    def wrap_reminder(self, action: ResultAction, body: dict[str, Any]) -> dict[str, Any]:
        """Encapsule une action différée dans un message ``$_reminder``."""
        return {
            "Uuid": str(action.uuid),
            "Name": constants.PUSH_REMINDER,
            "Kind": constants.PUSH_ACTION_NAME,
            "Delay": action.delay,
            "Message": body,
        }
