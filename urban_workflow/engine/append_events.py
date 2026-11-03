"""Chaîne de responsabilité décidant où l'événement s'insère.

Portage de ``AppendEvents/`` : l'événement standard est ajouté à
l'historique du workflow ; l'événement technique ``$_result`` (résultat
d'une action poussée) ne crée pas d'entrée d'historique mais accroche le
message de résultat à l'action d'origine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .. import constants
from ..models import ChangeEnum, RunContext


class AppendEventResponsibility(ABC):
    """Maillon de la chaîne (portage de ``Responsability<TContext>``)."""

    def __init__(self, child: Optional["AppendEventResponsibility"] = None) -> None:
        self.child = child

    def eval(self, ctx: RunContext) -> None:
        if self.check(ctx):
            self.execute(ctx)
        elif self.child is not None:
            self.child.eval(ctx)

    @abstractmethod
    def check(self, ctx: RunContext) -> bool: ...

    @abstractmethod
    def execute(self, ctx: RunContext) -> None: ...


class AppendStandardEvent(AppendEventResponsibility):
    """Cas général : l'événement rejoint l'historique du workflow."""

    def check(self, ctx: RunContext) -> bool:
        return True

    def execute(self, ctx: RunContext) -> None:
        ctx.workflow.events.append(ctx.event)


class AppendResultActionEvent(AppendEventResponsibility):
    """``$_result`` : rattache le résultat à l'action poussée d'origine.

    L'événement entrant porte ``EventId`` et ``TaskId`` dans ses données
    étendues ; le message de résultat (dates + données étendues de
    l'entrant) est posé sur la :class:`~urban_workflow.models.PushedAction`
    correspondante.
    """

    def check(self, ctx: RunContext) -> bool:
        return ctx.event.name == constants.RESULT_ACTION_NAME

    def execute(self, ctx: RunContext) -> None:
        datas = ctx.event.extended_datas
        event_id = datas.get(constants.EVENT_ID)
        task_id = datas.get(constants.TASK_UUID)
        if event_id is None or task_id is None:
            return

        event = ctx.workflow.get_event(UUID(str(event_id)))
        if event is None:
            return

        action = event.get_action(UUID(str(task_id)))
        if action is None:
            return

        incoming = ctx.incoming_event
        body = {
            "CreationDate": str(incoming.creation_date),
            "EventDate": str(incoming.event_date),
        }
        body.update(incoming.extended_datas)

        action.change = ChangeEnum.NEW
        action.result_message = body
