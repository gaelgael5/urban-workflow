"""Traducteur d'actions sur templates urban-json.

Portage de ``WorkflowProcessor.TranslateActions`` : corps du message par
template JSLT (nom d'action → template, défaut sinon), en-têtes par le
registre de métadonnées, et encapsulation ``$_reminder`` des actions
différées. Le message produit a la forme ``MessageRaw`` du source :
``{"Header": {...}, "Body": {...}}``.
"""

from __future__ import annotations

from typing import Optional

from .. import constants
from ..engine.translator import ActionTranslator
from ..models import ChangeEnum, PushedAction, ResultAction, RunContext
from .context import build_action_document
from .metadata import MetadataRegistry
from .registry import TemplateRegistry


class JsltActionTranslator(ActionTranslator):
    """Matérialise les actions collectées via les templates JSLT."""

    def __init__(
        self,
        templates: Optional[TemplateRegistry] = None,
        metadatas: Optional[MetadataRegistry] = None,
    ) -> None:
        self.templates = templates if templates is not None else TemplateRegistry()
        self.metadatas = metadatas if metadatas is not None else MetadataRegistry()

    def translate(self, ctx: RunContext, action: ResultAction) -> PushedAction:

        document = build_action_document(ctx, action)
        body = self.templates.transform(action.name, document)
        header = self.metadatas.get(action.name)

        if action.delay > 0:
            # Action différée : le corps réel est encapsulé dans un message
            # de rappel $_reminder (bus de rappel différé).
            reminder = ResultAction(
                uuid=action.uuid,
                name=constants.PUSH_REMINDER,
                kind=constants.PUSH_ACTION_NAME,
                delay=action.delay,
                event=action.event,
                event_date=action.event_date,
            )
            wrapper = self.templates.transform(
                constants.PUSH_REMINDER, build_action_document(ctx, reminder)
            )
            if isinstance(wrapper, dict):
                wrapper["Message"] = body
            body = wrapper
            header = self.metadatas.get(constants.PUSH_REMINDER)

        return PushedAction(
            uuid=action.uuid,
            name=action.name,
            kind=action.kind,
            change=ChangeEnum.NEW,
            execute_message={"Header": header, "Body": body},
        )
