"""Désérialisation des événements entrants.

Portage de ``PartialJsonWorkflowSerializer.Populate`` : les propriétés
connues de l'événement (``Name``, ``Uuid``, ``ExternalId``,
``CreationDate``, ``EventDate`` — noms CamelCase du format source) sont
affectées aux champs typés, tout le reste part dans ``extended_datas``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from ..models import IncomingEvent

Payload = str | Mapping[str, Any]


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _parse_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


_KNOWN_FIELDS = {
    "Name": ("name", str),
    "Uuid": ("uuid", _parse_uuid),
    "ExternalId": ("external_id", str),
    "CreationDate": ("creation_date", _parse_datetime),
    "EventDate": ("event_date", _parse_datetime),
}


def populate_incoming_event(event: IncomingEvent, payload: Payload) -> IncomingEvent:
    """Peuple ``event`` depuis un payload JSON (chaîne ou mapping).

    Lève ``ValueError`` si le payload n'est pas un objet JSON ou si une
    propriété connue est invalide — le moteur enveloppe en
    :class:`~urban_workflow.exceptions.InvalidIncomingEventFormatError`.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, Mapping):
        raise ValueError("incoming event payload must be a JSON object")

    for key, value in payload.items():
        known = _KNOWN_FIELDS.get(key)
        if known is not None:
            attribute, convert = known
            setattr(event, attribute, convert(value))
        else:
            event.extended_datas[key] = value

    return event


def parse_incoming_event(payload: Payload) -> IncomingEvent:
    """Construit un :class:`IncomingEvent` depuis un payload JSON."""
    return populate_incoming_event(IncomingEvent(), payload)


def event_to_document(event: IncomingEvent) -> dict[str, Any]:
    """Reconstruit le document « format fil » d'un événement entrant.

    Propriétés du socle en CamelCase + données étendues — c'est ce
    document que les schémas d'événements valident et sur lequel le hash
    anti-doublon (``x-dedup``) est calculé.
    """
    document: dict[str, Any] = dict(event.extended_datas)
    document["Name"] = event.name
    document["Uuid"] = str(event.uuid)
    document["ExternalId"] = event.external_id
    if event.creation_date is not None:
        document["CreationDate"] = event.creation_date.isoformat()
    if event.event_date is not None:
        document["EventDate"] = event.event_date.isoformat()
    return document
