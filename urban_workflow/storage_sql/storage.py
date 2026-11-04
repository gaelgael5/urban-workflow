"""Stockage SQL des agrégats workflow (SQLAlchemy Core).

Un workflow est persisté en trois tables (workflow, événements, actions) et
rechargé comme agrégat complet. Les écritures sont idempotentes (upsert par
clé) : rejouer une sauvegarde ne crée pas de doublon.

Note de fidélité : le ``WorkflowStoreSql`` du source écrivait les données
du workflow dans la colonne ``DatasWorkflow`` à partir de la sérialisation
de **l'événement** (paramètre ``txtStep`` passé deux fois) — bug non
reproduit, les données de chaque niveau sont les siennes.
"""

from __future__ import annotations

import enum
import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, select
from sqlalchemy.engine import Connection

from ..models import ChangeEnum, Event, PushedAction, Workflow
from .schema import create_schema, workflow_actions, workflow_events, workflows


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    return str(value)


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _load(text: str | None) -> Any:
    return json.loads(text) if text else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_date(text: str | None) -> datetime | None:
    return datetime.fromisoformat(text) if text else None


class SqlWorkflowStorage:
    """Persistance des workflows sur un moteur SQLAlchemy.

    ``engine`` : un ``Engine`` SQLAlchemy ou une URL (``sqlite:///…``,
    ``postgresql+psycopg://…``).
    """

    def __init__(self, engine: Engine | str) -> None:
        if isinstance(engine, str):
            from sqlalchemy import create_engine

            engine = create_engine(engine)
        self.engine: Engine = engine

    def create_schema(self) -> SqlWorkflowStorage:
        create_schema(self.engine)
        return self

    # ------------------------------------------------------------------
    # Lecture (dont le callback du processor)
    # ------------------------------------------------------------------

    def load_by_external_id(self, external_id: str) -> list[Workflow]:
        """Les workflows d'un sujet — à brancher tel quel sur
        ``processor.load_existing_workflows_by_external_id``."""
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(workflows).where(workflows.c.external_id == external_id)
            ).mappings()
            return [self._build_workflow(connection, row) for row in rows]

    def get(self, uuid: UUID | str) -> Workflow | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(workflows).where(workflows.c.uuid == str(uuid))
                )
                .mappings()
                .first()
            )
            return self._build_workflow(connection, row) if row else None

    def get_all(self) -> list[Workflow]:
        with self.engine.connect() as connection:
            rows = connection.execute(select(workflows)).mappings()
            return [self._build_workflow(connection, row) for row in rows]

    # ------------------------------------------------------------------
    # Écriture (agrégat complet, idempotente)
    # ------------------------------------------------------------------

    def save_workflow(
        self, workflow: Workflow, connection: Connection | None = None
    ) -> None:
        """Upsert du workflow, de ses événements et de leurs actions.

        Sans ``connection``, ouvre une transaction dédiée ; avec, s'inscrit
        dans la transaction appelante (chaîne de sorties).
        """
        if connection is None:
            with self.engine.begin() as owned:
                self._save(owned, workflow)
        else:
            self._save(connection, workflow)

    def _save(self, connection: Connection, workflow: Workflow) -> None:
        self._upsert(
            connection,
            workflows,
            {
                "uuid": str(workflow.uuid),
                "external_id": workflow.external_id,
                "workflow_name": workflow.workflow_name,
                "version": workflow.version,
                "concurrency": workflow.concurrency,
                "recursive": workflow.recursive,
                "current_state": workflow.current_state,
                "creation_date": _iso(workflow.creation_date),
                "last_update_date": _iso(workflow.last_update_date),
                "extended_datas": _dump(workflow.extended_datas),
            },
        )

        for position, event in enumerate(workflow.events):
            self._upsert(
                connection,
                workflow_events,
                {
                    "uuid": str(event.uuid),
                    "workflow_uuid": str(workflow.uuid),
                    "position": position,
                    "name": event.name,
                    "from_state": event.from_state,
                    "to_state": event.to_state,
                    "creation_date": _iso(event.creation_date),
                    "event_date": _iso(event.event_date),
                    "dedup_hash": event.dedup_hash,
                    "extended_datas": _dump(event.extended_datas),
                },
            )
            for action_position, action in enumerate(event.actions):
                self._upsert(
                    connection,
                    workflow_actions,
                    {
                        "uuid": str(action.uuid),
                        "event_uuid": str(event.uuid),
                        "position": action_position,
                        "name": action.name,
                        "kind": action.kind,
                        "execute_message": _dump(action.execute_message)
                        if action.execute_message is not None
                        else None,
                        "result_message": _dump(action.result_message)
                        if action.result_message is not None
                        else None,
                        "cancel_message": _dump(action.cancel_message)
                        if action.cancel_message is not None
                        else None,
                        "result_cancel_message": _dump(action.result_cancel_message)
                        if action.result_cancel_message is not None
                        else None,
                    },
                )

    @staticmethod
    def _upsert(connection: Connection, table, row: dict[str, Any]) -> None:
        key = row["uuid"]
        exists = connection.execute(
            select(table.c.uuid).where(table.c.uuid == key)
        ).first()
        if exists:
            connection.execute(
                table.update().where(table.c.uuid == key).values(**row)
            )
        else:
            connection.execute(table.insert().values(**row))

    # ------------------------------------------------------------------
    # Reconstruction des agrégats
    # ------------------------------------------------------------------

    def _build_workflow(self, connection: Connection, row) -> Workflow:
        workflow = Workflow(
            uuid=UUID(row["uuid"]),
            external_id=row["external_id"],
            workflow_name=row["workflow_name"],
            version=row["version"],
            concurrency=row["concurrency"],
            recursive=bool(row["recursive"]),
            creation_date=_parse_date(row["creation_date"]),
            last_update_date=_parse_date(row["last_update_date"]),
            change=ChangeEnum.NONE,
            extended_datas=json.loads(row["extended_datas"] or "{}"),
        )

        event_rows = connection.execute(
            select(workflow_events)
            .where(workflow_events.c.workflow_uuid == row["uuid"])
            .order_by(workflow_events.c.position)
        ).mappings()

        for event_row in event_rows:
            event = Event(
                uuid=UUID(event_row["uuid"]),
                name=event_row["name"],
                from_state=event_row["from_state"],
                to_state=event_row["to_state"],
                creation_date=_parse_date(event_row["creation_date"]),
                event_date=_parse_date(event_row["event_date"]),
                dedup_hash=event_row["dedup_hash"] or "",
                change=ChangeEnum.NONE,
                extended_datas=json.loads(event_row["extended_datas"] or "{}"),
            )

            action_rows = connection.execute(
                select(workflow_actions)
                .where(workflow_actions.c.event_uuid == event_row["uuid"])
                .order_by(workflow_actions.c.position)
            ).mappings()

            for action_row in action_rows:
                event.actions.append(
                    PushedAction(
                        uuid=UUID(action_row["uuid"]),
                        name=action_row["name"],
                        kind=action_row["kind"],
                        change=ChangeEnum.NONE,
                        execute_message=_load(action_row["execute_message"]),
                        result_message=_load(action_row["result_message"]),
                        cancel_message=_load(action_row["cancel_message"]),
                        result_cancel_message=_load(
                            action_row["result_cancel_message"]
                        ),
                    )
                )

            workflow.events.append(event)

        return workflow
