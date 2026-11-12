"""Schéma SQL — reprise du schéma logique du source.

Tables ``Workflows`` / ``WorkflowEvents`` / ``WorkflowActions`` du script
SQL Server d'origine, transposées en SQLAlchemy Core neutre :

- clés UUID stockées en chaînes (36) ;
- dates en ISO 8601 (chaînes) pour préserver le fuseau sur tous les
  dialectes (l'équivalent du ``datetimeoffset`` SQL Server) ;
- données étendues et messages en JSON (``Text``).

La table ``Locks`` du source n'est pas reprise : le verrouillage est
porté par :class:`~urban_workflow.outputs.LockObject` (implémentation
distribuée à brancher selon l'infrastructure).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Index, Integer, MetaData, String, Table, Text

metadata = MetaData()

workflows = Table(
    "workflows",
    metadata,
    Column("uuid", String(36), primary_key=True),
    Column("external_id", String(80), nullable=False),
    Column("workflow_name", String(70), nullable=False),
    Column("version", Integer, nullable=False),
    Column("concurrency", Integer, nullable=False, default=1),
    Column("recursive", Boolean, nullable=False, default=False),
    Column("current_state", String(70), nullable=False, default=""),
    Column("creation_date", String(40)),
    Column("last_update_date", String(40)),
    Column("extended_datas", Text, nullable=False, default="{}"),
    Index("ix_workflows_external_id", "external_id"),
)

workflow_events = Table(
    "workflow_events",
    metadata,
    Column("uuid", String(36), primary_key=True),
    Column("workflow_uuid", String(36), nullable=False),
    Column("position", Integer, nullable=False),
    Column("name", String(70), nullable=False),
    Column("from_state", String(70), nullable=False, default=""),
    Column("to_state", String(70), nullable=False, default=""),
    Column("creation_date", String(40)),
    Column("event_date", String(40)),
    Column("integration_date", String(40)),
    Column("dedup_hash", String(64), nullable=False, default=""),
    Column("extended_datas", Text, nullable=False, default="{}"),
    Index("ix_workflow_events_workflow_uuid", "workflow_uuid"),
)

workflow_actions = Table(
    "workflow_actions",
    metadata,
    Column("uuid", String(36), primary_key=True),
    Column("event_uuid", String(36), nullable=False),
    Column("position", Integer, nullable=False),
    Column("name", String(70), nullable=False),
    Column("kind", String(40), nullable=False, default=""),
    Column("execute_message", Text),
    Column("result_message", Text),
    Column("cancel_message", Text),
    Column("result_cancel_message", Text),
    Index("ix_workflow_actions_event_uuid", "event_uuid"),
)

# Extension urban-workflow (absente du source) : une instance par SWITCH.
workflow_states = Table(
    "workflow_states",
    metadata,
    Column("uuid", String(36), primary_key=True),
    Column("workflow_uuid", String(36), nullable=False),
    Column("position", Integer, nullable=False),
    Column("name", String(70), nullable=False),
    Column("creation_date", String(40)),
    Column("event_uuid", String(36)),
    Column("extended_datas", Text, nullable=False, default="{}"),
    Index("ix_workflow_states_workflow_uuid", "workflow_uuid"),
)


def create_schema(engine) -> None:
    """Crée les tables si elles n'existent pas."""
    metadata.create_all(engine)
