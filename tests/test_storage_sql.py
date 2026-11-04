"""Persistance SQL (extra ``[sql]``) — intégration SQLite en mémoire.

Sautés proprement si SQLAlchemy n'est pas installé.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine, select

from urban_workflow import (
    ChangeEnum,
    Event,
    IncomingEvent,
    IncomingEventConfig,
    InitializationOnEventConfig,
    PushedAction,
    ResultActionConfig,
    StateConfig,
    TransitionConfig,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
    constants,
)
from urban_workflow.outputs import OutputBus
from urban_workflow.storage_sql import (
    SqlWorkflowStorage,
    sql_output,
)
from urban_workflow.storage_sql import (
    workflows as workflows_table,
)

NOW = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def storage() -> SqlWorkflowStorage:
    # SQLite en mémoire : le pool conserve la connexion, la base survit
    # aux connect/close successifs du test.
    return SqlWorkflowStorage(create_engine("sqlite://")).create_schema()


def make_workflow() -> Workflow:
    workflow = Workflow(
        workflow_name="wrk1",
        version=2,
        external_id="DA-1",
        concurrency=1,
        creation_date=NOW,
        last_update_date=NOW,
        extended_datas={"Country": "France", "Statut": "en cours"},
    )
    event = Event(
        name="Event1",
        from_state="",
        to_state="State1",
        creation_date=NOW,
        event_date=NOW,
        extended_datas={"Montant": 120},
    )
    event.actions.append(
        PushedAction(
            name="Cut",
            kind=constants.PUSH_ACTION_NAME,
            change=ChangeEnum.NEW,
            execute_message={"Header": {}, "Body": {"Name": "Cut"}},
        )
    )
    workflow.events.append(event)
    return workflow


class TestRoundTrip:
    def test_aggregate_round_trip(self, storage):
        saved = make_workflow()
        storage.save_workflow(saved)

        loaded = storage.load_by_external_id("DA-1")[0]

        assert loaded.uuid == saved.uuid
        assert loaded.workflow_name == "wrk1"
        assert loaded.version == 2
        assert loaded.current_state == "State1"
        assert loaded.creation_date == NOW
        assert loaded.extended_datas == {"Country": "France", "Statut": "en cours"}
        assert loaded.change is ChangeEnum.NONE

        event = loaded.events[0]
        assert event.uuid == saved.events[0].uuid
        assert event.extended_datas == {"Montant": 120}

        action = event.actions[0]
        assert action.name == "Cut"
        assert action.execute_message == {"Header": {}, "Body": {"Name": "Cut"}}
        assert action.result_message is None

    def test_save_is_idempotent_upsert(self, storage):
        workflow = make_workflow()
        storage.save_workflow(workflow)

        workflow.extended_datas["Statut"] = "approuvee"
        workflow.events[0].actions[0].result_message = {"Status": "done"}
        storage.save_workflow(workflow)

        loaded = storage.load_by_external_id("DA-1")
        assert len(loaded) == 1
        assert len(loaded[0].events) == 1
        assert len(loaded[0].events[0].actions) == 1
        assert loaded[0].extended_datas["Statut"] == "approuvee"
        assert loaded[0].events[0].actions[0].result_message == {"Status": "done"}

    def test_get_by_uuid_and_get_all(self, storage):
        workflow = make_workflow()
        storage.save_workflow(workflow)

        assert storage.get(workflow.uuid).uuid == workflow.uuid
        assert storage.get(uuid4()) is None
        assert [w.uuid for w in storage.get_all()] == [workflow.uuid]


# ----------------------------------------------------------------------
# Moteur complet sur stockage SQL
# ----------------------------------------------------------------------


class _ListBus(OutputBus):
    def __init__(self):
        self.pushed = []

    def push(self, action):
        self.pushed.append(action)


def make_engine(storage: SqlWorkflowStorage, bus: OutputBus = None) -> WorkflowEngine:
    configs = WorkflowsConfig().add_document(
        WorkflowConfigFixture.build()
    )
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = storage.load_by_external_id
    processor.output_actions = sql_output(storage, bus=bus)
    return WorkflowEngine(processor)


class WorkflowConfigFixture:
    @staticmethod
    def build():
        from urban_workflow import WorkflowConfig

        return (
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1")
                .add_incoming_actions(
                    None,
                    ResultActionConfig(name="act1", kind=constants.PUSH_ACTION_NAME),
                )
                .add_event(
                    IncomingEventConfig(name="evnt2").add_transition(
                        TransitionConfig(target_state_name="State2")
                    )
                )
            )
            .add_state(
                StateConfig(name="State2").add_incoming_actions(
                    None, ResultActionConfig(name="act2")
                )
            )
        )


class TestEngineOnSql:
    def test_lifecycle_across_evaluations(self, storage):
        engine = make_engine(storage)
        external_id = str(uuid4())

        # Création — persistée en SQL.
        engine.evaluate_event({"Name": "evnt1", "Uuid": str(uuid4()),
                               "ExternalId": external_id, "Pays": "France"})
        workflow = storage.load_by_external_id(external_id)[0]
        assert workflow.current_state == "State1"
        assert workflow.extended_datas["Pays"] == "France"

        # Transition — le workflow est rechargé depuis SQL puis re-persisté.
        engine.evaluate_event({"Name": "evnt2", "Uuid": str(uuid4()),
                               "ExternalId": external_id})
        workflow = storage.load_by_external_id(external_id)[0]
        assert workflow.current_state == "State2"
        assert len(workflow.events) == 2

        # L'action matérialisée de l'entrée en State1 est dans l'outbox SQL.
        action = workflow.events[0].actions[0]
        assert action.name == "act1"
        assert action.execute_message["Body"]["Name"] == "act1"

    def test_result_event_updates_persisted_action(self, storage):
        engine = make_engine(storage)
        external_id = str(uuid4())
        engine.evaluate_event({"Name": "evnt1", "Uuid": str(uuid4()),
                               "ExternalId": external_id})
        workflow = storage.load_by_external_id(external_id)[0]
        action = workflow.events[0].actions[0]

        engine.evaluate_event({
            "Name": constants.RESULT_ACTION_NAME,
            "Uuid": str(uuid4()),
            "ExternalId": external_id,
            constants.EVENT_ID: str(workflow.events[0].uuid),
            constants.TASK_UUID: str(action.uuid),
            "Status": "done",
        })

        workflow = storage.load_by_external_id(external_id)[0]
        assert len(workflow.events) == 1  # pas d'entrée d'historique pour $_result
        assert workflow.events[0].actions[0].result_message["Status"] == "done"

    def test_bus_receives_pushed_actions(self, storage):
        bus = _ListBus()
        engine = make_engine(storage, bus=bus)
        engine.evaluate_event({"Name": "evnt1", "Uuid": str(uuid4()),
                               "ExternalId": str(uuid4())})
        assert [a.name for a in bus.pushed] == ["act1"]

    def test_replay_does_not_duplicate(self, storage):
        engine = make_engine(storage)
        payload = {"Name": "evnt1", "Uuid": str(uuid4()), "ExternalId": str(uuid4())}
        engine.evaluate_event(payload)
        engine.evaluate_event(payload)  # rejeu : même Uuid

        loaded = storage.load_by_external_id(payload["ExternalId"])
        assert len(loaded) == 1
        assert len(loaded[0].events) == 1


# ----------------------------------------------------------------------
# Transaction réelle : rollback SQL effectif
# ----------------------------------------------------------------------


class _ExplodingBus(OutputBus):
    def push(self, action):
        raise RuntimeError("bus en panne")


class TestSqlTransaction:
    def test_rollback_leaves_no_rows(self, storage):
        # Le bus échoue APRÈS la persistance du modèle (il est dernier de
        # chaîne ici) : la transaction partagée doit tout annuler.
        from urban_workflow.outputs import BusOutputAction
        from urban_workflow.storage_sql import (
            SqlPushModelOutputAction,
            SqlUnitOfWork,
        )

        def failing_chain():
            unit_of_work = SqlUnitOfWork(storage)
            return SqlPushModelOutputAction(
                storage,
                unit_of_work,
                child=BusOutputAction(_ExplodingBus()),
            )

        configs = WorkflowsConfig().add_document(WorkflowConfigFixture.build())
        processor = WorkflowProcessor(configs, WorkflowFactory())
        processor.load_existing_workflows_by_external_id = storage.load_by_external_id
        processor.output_actions = failing_chain

        external_id = str(uuid4())
        with pytest.raises(RuntimeError, match="bus en panne"):
            processor.evaluate_event(
                IncomingEvent(name="evnt1", external_id=external_id)
            )

        # Le INSERT du workflow a été exécuté puis annulé : aucune ligne.
        with storage.engine.connect() as connection:
            rows = connection.execute(
                select(workflows_table).where(
                    workflows_table.c.external_id == external_id
                )
            ).all()
        assert rows == []
