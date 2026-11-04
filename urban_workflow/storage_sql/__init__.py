"""Persistance SQL (extra optionnel ``[sql]``, SQLAlchemy Core).

Remplace le micro-ORM maison du source (``Black.Beard.Workflows.Outputs.Sql``,
non porté — décision actée dans ``docs/analyse-portage.md``) en reprenant son
schéma logique : trois tables ``workflows`` / ``workflow_events`` /
``workflow_actions``, les données étendues et messages en JSON.

Usage ::

    from sqlalchemy import create_engine
    from urban_workflow.storage_sql import SqlWorkflowStorage, sql_output

    storage = SqlWorkflowStorage(create_engine("sqlite:///workflows.db"))
    storage.create_schema()

    processor.load_existing_workflows_by_external_id = storage.load_by_external_id
    processor.output_actions = sql_output(storage)   # bus optionnel : sql_output(storage, bus=...)

Nécessite ``sqlalchemy >= 2`` : ``pip install urban-workflow[sql]``.
"""

try:
    import sqlalchemy  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "urban_workflow.storage_sql nécessite SQLAlchemy : "
        "pip install urban-workflow[sql]"
    ) from exc

from .outputs import SqlPushModelOutputAction, SqlTransaction, SqlUnitOfWork, sql_output
from .schema import create_schema, metadata, workflow_actions, workflow_events, workflows
from .storage import SqlWorkflowStorage

__all__ = [
    "SqlPushModelOutputAction",
    "SqlTransaction",
    "SqlUnitOfWork",
    "SqlWorkflowStorage",
    "create_schema",
    "metadata",
    "sql_output",
    "workflow_actions",
    "workflow_events",
    "workflows",
]
