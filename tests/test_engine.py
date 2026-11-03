"""Tests du moteur — port de ``WorkflowsUnitTest.cs``, ``WorkflowsConfigUnitTest1.cs``
et ``IncomingEventUnitTest.cs``, plus les bugs §5 non reproduits.
"""

from __future__ import annotations

import zlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from urban_workflow import (
    ChangeEnum,
    IncomingEvent,
    IncomingEventConfig,
    InitializationOnEventConfig,
    InvalidIncomingEventFormatError,
    LockFailedError,
    MemoryLocker,
    MemoryStorage,
    OutputAction,
    PushedAction,
    ResultActionConfig,
    StateConfig,
    Transaction,
    TransitionConfig,
    Workflow,
    WorkflowClock,
    WorkflowConfig,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
    constants,
    parse_incoming_event,
)
from urban_workflow.outputs import DoNothingTransaction, default_memory_output


def make_processor(configs: WorkflowsConfig, storage: MemoryStorage) -> WorkflowProcessor:
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return processor


def make_event(name: str, external_id: str, **extended) -> IncomingEvent:
    return IncomingEvent(
        name=name,
        uuid=uuid4(),
        external_id=external_id,
        creation_date=WorkflowClock.now(),
        event_date=WorkflowClock.now(),
        extended_datas=dict(extended),
    )


# ----------------------------------------------------------------------
# Port de WorkflowsUnitTest (configuration fluide, sans DSL)
# ----------------------------------------------------------------------


class TestWorkflowProcessor:
    def test_initialize_workflow_recursive(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", label="wrk1 config", version=1)
            .add_initializer(
                InitializationOnEventConfig(
                    event_name="evnt1", recursive=True
                ).add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1", label="State1").add_event(
                    IncomingEventConfig(name="evnt1").add_transition(
                        TransitionConfig(target_state_name="State2")
                    )
                )
            )
            .add_state(StateConfig(name="State2", label="State2"))
        )

        processor = make_processor(configs, storage)
        event = make_event("evnt1", str(uuid4()))
        processor.evaluate_event(event)

        workflow = storage.get_by(Workflow, event.external_id, "external_id")[0]
        assert workflow.current_state == "State2"
        assert workflow.change is ChangeEnum.NEW
        assert len(workflow.events) == 1

    def test_initialize_workflow_with_rule(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1").add_event(
                    IncomingEventConfig(name="evnt2").add_transition(
                        TransitionConfig(
                            target_state_name="State2",
                            when_rule=lambda c: c.incoming_event.name == "evnt2",
                        )
                    )
                )
            )
            .add_state(StateConfig(name="State2"))
        )
        processor = make_processor(configs, storage)

        event1 = make_event("evnt1", str(uuid4()))
        processor.evaluate_event(event1)
        workflow = storage.get_by(Workflow, event1.external_id, "external_id")[0]
        assert workflow.current_state == "State1"

        # evnt2 sur un autre ExternalId : pas d'initialiseur → rien de créé.
        event2 = make_event("evnt2", str(uuid4()))
        processor.evaluate_event(event2)
        assert storage.get_by(Workflow, event2.external_id, "external_id") == []

    def test_initialize_workflow_with_pushed_actions(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(
                    event_name="evnt1", recursive=True
                ).add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1")
                .add_incoming_actions(None, ResultActionConfig(name="act_on_state_in_1"))
                .add_outcoming_actions(None, ResultActionConfig(name="act_on_state_out"))
                .add_event(
                    IncomingEventConfig(name="evnt1")
                    .add_action(None, ResultActionConfig(name="act_on_event"))
                    .add_transition(
                        TransitionConfig(target_state_name="State2").add_actions(
                            None, ResultActionConfig(name="act_on_transition")
                        )
                    )
                )
            )
            .add_state(
                StateConfig(name="State2").add_incoming_actions(
                    None,
                    ResultActionConfig(name="act_on_state_in_2").add_argument(
                        "name", "@Event.Name"
                    ),
                )
            )
        )
        processor = make_processor(configs, storage)

        event = make_event("evnt1", str(uuid4()))
        processor.evaluate_event(event)

        workflow = storage.get_by(Workflow, event.external_id, "external_id")[0]
        actions = {action.name: action for action in workflow.last_event.actions}
        assert set(actions) == {
            "act_on_state_in_1",
            "act_on_event",
            "act_on_transition",
            "act_on_state_out",
            "act_on_state_in_2",
        }

        # L'argument @Event.Name est résolu à la traduction.
        in_2 = actions["act_on_state_in_2"]
        assert in_2.execute_message["Arguments"] == {"name": "evnt1"}
        assert in_2.change is ChangeEnum.NEW

    def test_switch_state(self):
        external_id = str(uuid4())
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(
                    event_name="evnt1", recursive=True
                ).add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1").add_event(
                    IncomingEventConfig(name="evnt1").add_transition(
                        TransitionConfig(target_state_name="State2")
                    )
                )
            )
            .add_state(
                StateConfig(name="State2")
                .add_outcoming_actions(None, ResultActionConfig(name="act1"))
                .add_event(
                    IncomingEventConfig(name="evnt2").add_transition(
                        TransitionConfig(target_state_name="State3")
                    )
                )
            )
            .add_state(
                StateConfig(name="State3").add_incoming_actions(
                    None, ResultActionConfig(name="act2")
                )
            )
        )
        processor = make_processor(configs, storage)

        processor.evaluate_event(make_event("evnt1", external_id))
        workflow = storage.get_by(Workflow, external_id, "external_id")[0]
        assert workflow.current_state == "State2"

        processor.evaluate_event(make_event("evnt2", external_id))
        workflow = storage.get_by(Workflow, external_id, "external_id")[0]
        assert workflow.current_state == "State3"
        names = [action.name for action in workflow.last_event.actions]
        assert "act1" in names
        assert "act2" in names

    def test_event_not_integrated_twice(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1").add_event(
                    IncomingEventConfig(name="evnt1").add_transition(
                        TransitionConfig(target_state_name="State1")
                    )
                )
            )
        )
        processor = make_processor(configs, storage)

        event = make_event("evnt1", str(uuid4()))
        processor.evaluate_event(event)
        workflow = storage.get_by(Workflow, event.external_id, "external_id")[0]
        assert len(workflow.events) == 1

        # Le même uuid d'événement n'est ni réintégré dans l'historique,
        # ni autorisé à recréer un workflow via l'initialiseur (rejeu).
        processor.evaluate_event(event)
        workflows = storage.get_by(Workflow, event.external_id, "external_id")
        assert len(workflows) == 1
        assert len(workflows[0].events) == 1

    def test_concurrency_guard_is_strict(self):
        # Bug §5-like non reproduit : le source autorisait une instance de
        # plus que CONCURENCY (comparaison <=).
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1, concurrency=2)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(StateConfig(name="State1"))
        )
        processor = make_processor(configs, storage)
        external_id = str(uuid4())

        for _ in range(3):
            processor.evaluate_event(make_event("evnt1", external_id))

        workflows = storage.get_by(Workflow, external_id, "external_id")
        assert len(workflows) == 2
        assert sorted(w.concurrency for w in workflows) == [1, 2]

    def test_result_action_event_attaches_result_message(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1").add_incoming_actions(
                    None,
                    ResultActionConfig(name="act1", kind=constants.PUSH_ACTION_NAME),
                )
            )
        )
        processor = make_processor(configs, storage)

        event = make_event("evnt1", str(uuid4()))
        processor.evaluate_event(event)
        workflow = storage.get_by(Workflow, event.external_id, "external_id")[0]
        pushed = workflow.last_event.actions[0]

        result_event = make_event(
            constants.RESULT_ACTION_NAME,
            event.external_id,
            **{
                constants.EVENT_ID: str(workflow.last_event.uuid),
                constants.TASK_UUID: str(pushed.uuid),
                "Status": "done",
            },
        )
        processor.evaluate_event(result_event)

        workflow = storage.get_by(Workflow, event.external_id, "external_id")[0]
        # $_result ne crée pas d'entrée d'historique…
        assert len(workflow.events) == 1
        # …mais accroche le résultat à l'action d'origine.
        action = workflow.last_event.actions[0]
        assert action.result_message["Status"] == "done"
        assert action.change is ChangeEnum.NEW


# ----------------------------------------------------------------------
# Transactions : rollback effectif (bug Dispose inversé non reproduit)
# ----------------------------------------------------------------------


class _RecordingTransaction(Transaction):
    def __init__(self, log):
        super().__init__()
        self._log = log

    def _commit_impl(self):
        self._log.append("commit")

    def _rollback_impl(self):
        self._log.append("rollback")


class _FailingOutput(OutputAction):
    def __init__(self, log):
        super().__init__()
        self._log = log

    def _prepare_impl(self, ctx):
        pass

    def _execute_impl(self):
        raise RuntimeError("boom")

    def _begin_transaction_impl(self):
        return _RecordingTransaction(self._log)


class TestTransactions:
    def test_rollback_on_failed_execute(self):
        log = []
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(StateConfig(name="State1"))
        )
        processor = WorkflowProcessor(configs, WorkflowFactory())
        processor.output_actions = lambda: _FailingOutput(log)

        with pytest.raises(RuntimeError, match="boom"):
            processor.evaluate_event(make_event("evnt1", str(uuid4())))

        assert log == ["rollback"]

    def test_context_manager_rolls_back_without_commit(self):
        transaction = DoNothingTransaction()
        with transaction:
            pass
        assert transaction.rolled_back is True

        transaction = DoNothingTransaction()
        with transaction:
            transaction.commit()
        assert transaction.rolled_back is False
        assert transaction.committed is True

    def test_commit_and_rollback_chain_to_children(self):
        log = []
        parent = _RecordingTransaction(log)
        parent.child = _RecordingTransaction(log)
        parent.commit()
        assert log == ["commit", "commit"]

        log.clear()
        parent = _RecordingTransaction(log)
        parent.child = _RecordingTransaction(log)
        parent.rollback()
        parent.rollback()  # idempotent
        assert log == ["rollback", "rollback"]


# ----------------------------------------------------------------------
# WorkflowEngine : verrous, compteur d'usage, format des payloads
# ----------------------------------------------------------------------


def make_engine(storage: MemoryStorage, **engine_kwargs) -> WorkflowEngine:
    configs = WorkflowsConfig().add_document(
        WorkflowConfig(name="wrk1", version=1)
        .add_initializer(
            InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
        )
        .add_state(StateConfig(name="State1"))
    )
    return WorkflowEngine(make_processor(configs, storage), **engine_kwargs)


class TestWorkflowEngine:
    def test_evaluate_event_from_dict_payload(self):
        storage = MemoryStorage()
        engine = make_engine(storage)

        contexts = engine.evaluate_event(
            {
                "Name": "evnt1",
                "Uuid": str(uuid4()),
                "ExternalId": "ext-1",
                "CreationDate": "2026-11-03T10:00:00+00:00",
                "EventDate": "2026-11-03T09:55:00Z",
                "Country": "France",
            }
        )

        assert len(contexts) == 1
        workflow = storage.get_by(Workflow, "ext-1", "external_id")[0]
        assert workflow.current_state == "State1"
        assert workflow.extended_datas["Country"] == "France"
        assert engine.can_be_removed is True

    def test_evaluate_event_from_json_string(self):
        storage = MemoryStorage()
        engine = make_engine(storage)
        engine.evaluate_event(
            '{"Name": "evnt1", "Uuid": "%s", "ExternalId": "ext-2"}' % uuid4()
        )
        assert storage.get_by(Workflow, "ext-2", "external_id")

    def test_invalid_payload_raises_format_error(self):
        engine = make_engine(MemoryStorage())
        with pytest.raises(InvalidIncomingEventFormatError):
            engine.evaluate_event("ceci n'est pas du JSON")
        with pytest.raises(InvalidIncomingEventFormatError):
            engine.evaluate_event('["pas", "un", "objet"]')

    def test_unregistered_incoming_type_raises_format_error(self):
        engine = make_engine(MemoryStorage())
        with pytest.raises(InvalidIncomingEventFormatError):
            engine.evaluate_event('{"Name": "evnt1"}', incoming_type="unknown")

    def test_registered_incoming_type_is_used(self):
        # Bug §5 non reproduit : CreateBaseIncomingEvent inversait le test
        # sur le type nommé (NullReferenceException sur le chemin nominal).
        class SpecialEvent(IncomingEvent):
            pass

        factory = WorkflowFactory()
        factory.add_incoming_event("special", SpecialEvent)
        event = factory.create_base_incoming_event(
            {"Name": "evnt1", "ExternalId": "x"}, "special"
        )
        assert isinstance(event, SpecialEvent)
        assert event.name == "evnt1"

    def test_lock_failed_when_key_already_locked(self):
        storage = MemoryStorage()
        locker = MemoryLocker(timeout=0.05)
        engine = make_engine(storage, locker=locker)

        crc = zlib.crc32(b"ext-locked")
        locker.lock(crc)
        try:
            with pytest.raises(LockFailedError):
                engine.evaluate_event(
                    {"Name": "evnt1", "Uuid": str(uuid4()), "ExternalId": "ext-locked"}
                )
        finally:
            locker.unlock(crc)

        # Le compteur d'usage redescend même après échec (bug Decrement
        # du source non reproduit).
        assert engine.can_be_removed is True


# ----------------------------------------------------------------------
# Port de IncomingEventUnitTest : désérialisation des payloads
# ----------------------------------------------------------------------


class TestParseIncomingEvent:
    def test_unserialize_event_incoming(self):
        payload = """{
            "Name": "evnt1",
            "Uuid": "352d5082-3fb9-4db8-8a59-bc864ade4929",
            "ExternalId": "c65ea000-dce0-44a3-a6f3-9daf7eebaefe",
            "CreationDate": "2019-09-23T09:48:52.186847+02:00",
            "EventDate": "2019-09-23T09:48:47.304792+02:00",
            "Site": "site1",
            "infos": { "name": "toto" },
            "infos2": [ { "name": "toto" }, { "name": "titi" } ]
        }"""

        event = parse_incoming_event(payload)

        assert event.name == "evnt1"
        assert event.uuid == UUID("352d5082-3fb9-4db8-8a59-bc864ade4929")
        assert event.external_id == "c65ea000-dce0-44a3-a6f3-9daf7eebaefe"
        assert event.creation_date.year == 2019
        assert event.event_date is not None
        # Seules les propriétés inconnues partent en données étendues.
        assert set(event.extended_datas) == {"Site", "infos", "infos2"}
        assert event.extended_datas["infos"] == {"name": "toto"}
        assert event.extended_datas["infos2"][1] == {"name": "titi"}

    def test_datetime_and_uuid_objects_pass_through(self):
        now = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
        uuid = uuid4()
        event = parse_incoming_event(
            {"Name": "e", "Uuid": uuid, "CreationDate": now, "EventDate": now}
        )
        assert event.uuid == uuid
        assert event.creation_date is now


# ----------------------------------------------------------------------
# Port de WorkflowsConfigUnitTest1 : sélection des configurations
# ----------------------------------------------------------------------


class TestWorkflowsConfigRouting:
    def test_routing_by_matching_filter(self):
        configs = (
            WorkflowsConfig()
            .add_document(
                WorkflowConfig(name="wrk1", version=1).add_filter("Country", "France")
            )
            .add_document(
                WorkflowConfig(name="wrk2", version=1).add_filter("Country", "Germany")
            )
        )

        event = make_event("evnt1", str(uuid4()), Country="Germany")
        matched = list(configs.matching(event))
        assert [config.name for config in matched] == ["wrk2"]

    def test_get_by_name_and_version(self):
        configs = (
            WorkflowsConfig()
            .add_document(WorkflowConfig(name="wrk1", version=1))
            .add_document(WorkflowConfig(name="wrk1", version=2))
        )
        assert configs.get("wrk1", 2).version == 2
        assert configs.get("wrk1", 1).version == 1
        assert len(configs.get_all("wrk1")) == 2


# ----------------------------------------------------------------------
# Rappels différés : encapsulation $_reminder par le traducteur par défaut
# ----------------------------------------------------------------------


class TestDefaultTranslator:
    def test_delayed_action_is_wrapped_in_reminder(self):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(
            WorkflowConfig(name="wrk1", version=1)
            .add_initializer(
                InitializationOnEventConfig(event_name="evnt1").add_switch("State1")
            )
            .add_state(
                StateConfig(name="State1").add_incoming_actions(
                    None,
                    ResultActionConfig(
                        name="remind_me",
                        kind=constants.PUSH_ACTION_NAME,
                        delay=120,
                    ),
                )
            )
        )
        processor = make_processor(configs, storage)
        processor.evaluate_event(make_event("evnt1", str(uuid4())))

        pushed = storage.get_all(PushedAction)[0]
        message = pushed.execute_message
        assert message["Name"] == constants.PUSH_REMINDER
        assert message["Delay"] == 120
        assert message["Message"]["Name"] == "remind_me"
