"""Document JSON de contexte d'une action (source des templates JSLT).

C'est le « document source par action » de l'analyse §3 : le contexte
d'exécution sérialisé une fois en structures JSON-compatibles, sur lequel
les templates naviguent avec JSONPath (``$.action.uuid``,
``$.workflow.external_id``, ``$.incoming.Country``…).
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any
from uuid import UUID

from ..clock import WorkflowClock
from ..models import ResultAction, RunContext


def json_safe(value: Any) -> Any:
    """Convertit récursivement ``value`` en structures JSON-compatibles.

    ``datetime``/``date`` → ISO 8601, ``UUID`` → chaîne, ``Enum`` → valeur ;
    dicts, listes et tuples sont parcourus, le reste passe tel quel.
    """
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    return value


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def build_action_document(ctx: RunContext, action: ResultAction) -> dict[str, Any]:
    """Construit le document JSON de contexte pour ``action``.

    Structure : ``action`` / ``workflow`` / ``event`` / ``incoming`` /
    ``now``. Les données étendues sont fusionnées dans leur section (clés
    CamelCase des payloads), les champs normalisés snake_case ayant
    priorité en cas de collision.
    """

    event = action.event if action.event is not None else ctx.event
    workflow = ctx.workflow
    incoming = ctx.incoming_event

    document: dict[str, Any] = {
        "action": {
            "uuid": str(action.uuid),
            "name": action.name,
            "label": action.label,
            "kind": action.kind,
            "delay": action.delay,
            "arguments": json_safe(action.resolve_arguments(ctx)),
        },
        "workflow": None,
        "event": None,
        "incoming": None,
        "now": WorkflowClock.now().isoformat(),
    }

    if workflow is not None:
        document["workflow"] = {
            **json_safe(workflow.extended_datas),
            "uuid": str(workflow.uuid),
            "name": workflow.workflow_name,
            "version": workflow.version,
            "external_id": workflow.external_id,
            "state": workflow.current_state,
        }

    if event is not None:
        document["event"] = {
            **json_safe(event.extended_datas),
            "uuid": str(event.uuid),
            "name": event.name,
            "from_state": event.from_state,
            "to_state": event.to_state,
            "creation_date": _iso(event.creation_date),
            "event_date": _iso(event.event_date),
        }

    if incoming is not None:
        document["incoming"] = {
            **json_safe(incoming.extended_datas),
            "uuid": str(incoming.uuid),
            "name": incoming.name,
            "external_id": incoming.external_id,
            "creation_date": _iso(incoming.creation_date),
            "event_date": _iso(incoming.event_date),
        }

    return document
