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
    "DedupKey": ("dedup_key", str),
}

# Propriétés du socle que l'émetteur ne fixe pas : posées par le moteur.
# Lues dans un payload, elles sont ignorées (ni champ typé, ni donnée
# étendue) — sinon un émetteur pourrait antidater son intégration.
_SYSTEM_FIELDS = frozenset({"IntegrationDate"})


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
        if key in _SYSTEM_FIELDS:
            continue
        known = _KNOWN_FIELDS.get(key)
        if known is not None:
            # Un Uuid absent ou null laisse celui tiré par le modèle, et
            # l'événement reste « sans Uuid d'émetteur » : le moteur ne
            # dédoublonnera donc pas dessus.
            if key == "Uuid":
                if value is None:
                    continue
                event.uuid_from_payload = True
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
    if event.integration_date is not None:
        document["IntegrationDate"] = event.integration_date.isoformat()
    if event.dedup_key:
        document["DedupKey"] = event.dedup_key
    return document
