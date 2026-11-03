"""Tests des modèles d'exécution."""

from datetime import datetime, timezone

from urban_workflow import (
    ChangeEnum,
    Event,
    PushedAction,
    ResultAction,
    RunContext,
    Workflow,
    WorkflowClock,
)
from urban_workflow.values import ContextRef


def test_workflow_current_state_follows_last_event():
    workflow = Workflow(workflow_name="wrk1")
    assert workflow.current_state == ""
    assert workflow.last_event is None

    workflow.add_events(
        Event(name="evnt1", from_state="State1", to_state="State1"),
        Event(name="evnt2", from_state="State1", to_state="State2"),
    )
    assert workflow.current_state == "State2"
    assert workflow.last_event.name == "evnt2"


def test_workflow_get_event_by_uuid():
    event = Event(name="evnt1")
    workflow = Workflow().add_events(event)
    assert workflow.get_event(event.uuid) is event
    assert workflow.get_event(Event().uuid) is None


def test_event_actions():
    action = PushedAction(name="Cut", change=ChangeEnum.NEW)
    event = Event().add_actions(action)
    assert event.get_action(action.uuid) is action
    assert event.get_action(PushedAction().uuid) is None


def test_result_action_resolve_arguments():
    workflow = Workflow(external_id="ext-1")
    ctx = RunContext(workflow=workflow)
    action = ResultAction(
        name="Cut",
        arguments={"key": ContextRef.parse("@Workflow.ExternalId"), "mode": "hard"},
    )
    assert action.resolve_arguments(ctx) == {"key": "ext-1", "mode": "hard"}


def test_clock_frozen():
    instant = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    with WorkflowClock.frozen(instant):
        assert WorkflowClock.now() == instant
    assert WorkflowClock.now() != instant
