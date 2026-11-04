"""Scénarios de bout en bout *script DSL → événements → états*.

Port des scénarios moteur de ``ParserUnitTest.cs`` : TestFilter,
TestInitialize, TestInitializeWithJumpState, TestExpire — sur les scripts
golden de ``test_dsl.py``.
"""

from __future__ import annotations

from uuid import uuid4

from test_dsl import PAYLOAD, PAYLOAD2, get_config

from urban_workflow import (
    MemoryStorage,
    PushedAction,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
    constants,
)
from urban_workflow.outputs import default_memory_output


def make_engine(payload: str = PAYLOAD) -> tuple[WorkflowEngine, MemoryStorage]:
    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(get_config(payload))

    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)

    return WorkflowEngine(processor), storage


def payload_for(name: str, external_id: str, **extra) -> dict:
    return {
        "Name": name,
        "Uuid": str(uuid4()),
        "ExternalId": external_id,
        "CreationDate": "2026-11-03T10:00:00+00:00",
        "EventDate": "2026-11-03T09:55:00+00:00",
        **extra,
    }


class TestFilter:
    """Port de ParserUnitTest.TestFilter : filtres MATCHING et routage."""

    def test_event_without_country_is_ignored(self):
        engine, storage = make_engine()
        engine.evaluate_event(payload_for("Event1", str(uuid4())))
        assert storage.get_all(Workflow) == []

    def test_event_with_wrong_country_is_ignored(self):
        engine, storage = make_engine()
        engine.evaluate_event(payload_for("Event1", str(uuid4()), Country="Germany"))
        assert storage.get_all(Workflow) == []

    def test_unknown_event_name_is_ignored(self):
        engine, storage = make_engine()
        engine.evaluate_event(payload_for("Event666", str(uuid4()), Country="France"))
        assert storage.get_all(Workflow) == []

    def test_matching_event_creates_workflow(self):
        engine, storage = make_engine()
        engine.evaluate_event(payload_for("Event1", str(uuid4()), Country="France"))
        assert len(storage.get_all(Workflow)) == 1


class TestInitialize:
    """Port de ParserUnitTest.TestInitialize : création puis transition."""

    def test_initialize_then_switch(self):
        engine, storage = make_engine()
        external_id = str(uuid4())

        engine.evaluate_event(
            payload_for("Event1", external_id, Country="France", age=25)
        )
        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State1"
        assert workflow.extended_datas["Country"] == "France"

        engine.evaluate_event(
            payload_for("Event2", external_id, Country="France", age=25)
        )
        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State2"
        assert len(workflow.events) == 2


class TestInitializeWithJumpState:
    """Port de ParserUnitTest.TestInitializeWithJumpState : RECURSIVE."""

    def test_recursive_initializer_jumps_to_state2(self):
        engine, storage = make_engine(PAYLOAD2)

        engine.evaluate_event(
            payload_for("Event1", str(uuid4()), Country="France", Age=25)
        )

        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State2"


class TestExpire:
    """Port de ParserUnitTest.TestExpire : rappel différé puis expiration."""

    def test_expiration_moves_to_state3(self):
        engine, storage = make_engine()
        external_id = str(uuid4())

        engine.evaluate_event(payload_for("Event1", external_id, Country="France"))
        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State1"

        # À l'entrée de State1, le rappel d'expiration ($_reminder) a été
        # poussé sur le bus : 2 DAY → 2880 minutes.
        reminders = storage.get_all(PushedAction)
        assert len(reminders) == 1
        message = reminders[0].execute_message["Body"]
        assert message["Name"] == constants.PUSH_REMINDER
        assert message["Delay"] == 2 * 24 * 60
        assert message["Message"]["Name"] == constants.EXPIRED_EVENT_NAME

        # L'événement technique __expired, ciblé sur ce workflow et émis
        # alors que l'état n'a pas changé, bascule vers State3.
        engine.evaluate_event(
            payload_for(
                constants.EXPIRED_EVENT_NAME,
                external_id,
                WorkflowId=str(workflow.uuid),
                CurrentState="State1",
            )
        )
        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State3"

    def test_stale_expiration_is_ignored(self):
        engine, storage = make_engine()
        external_id = str(uuid4())

        engine.evaluate_event(payload_for("Event1", external_id, Country="France"))
        workflow = storage.get_all(Workflow)[0]

        # Rappel périmé : l'état courant indiqué ne correspond plus.
        engine.evaluate_event(
            payload_for(
                constants.EXPIRED_EVENT_NAME,
                external_id,
                WorkflowId=str(workflow.uuid),
                CurrentState="State0",
            )
        )
        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State1"
