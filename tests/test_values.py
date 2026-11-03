"""Tests des valeurs paresseuses (ContextRef, make_value, resolve_value)."""

import pytest

from urban_workflow import (
    ContextRef,
    Event,
    IncomingEvent,
    ResolutionArgumentError,
    RunContext,
    Workflow,
    make_value,
    resolve_value,
)


@pytest.fixture
def ctx() -> RunContext:
    workflow = Workflow(workflow_name="wrk1", external_id="ext-42")
    incoming = IncomingEvent(name="evnt1", external_id="ext-42")
    incoming.extended_datas["age"] = 21
    event = Event(name="evnt1", from_state="State1", to_state="State2")
    return RunContext(workflow=workflow, incoming_event=incoming, event=event)


def test_make_value_literal_passthrough():
    assert make_value("hello") == "hello"
    assert make_value(12) == 12
    assert make_value(None) is None


def test_make_value_at_prefix_becomes_ref():
    value = make_value("@Event.Name")
    assert isinstance(value, ContextRef)
    assert value.path == "Event.Name"


def test_ref_resolves_camelcase_dsl_path_on_snake_case_attributes(ctx):
    # Chemins tels qu'écrits dans le DSL source : @Event.ExternalId, @Workflow.Uuid…
    assert ContextRef.parse("@IncomingEvent.ExternalId")(ctx) == "ext-42"
    assert ContextRef.parse("@Workflow.WorkflowName")(ctx) == "wrk1"
    assert ContextRef.parse("@Event.ToState")(ctx) == "State2"


def test_ref_falls_back_to_extended_datas(ctx):
    # 'age' n'est pas un attribut d'IncomingEvent : résolu dans extended_datas.
    assert ContextRef.parse("@IncomingEvent.age")(ctx) == 21


def test_ref_missing_key_raises_with_path(ctx):
    with pytest.raises(ResolutionArgumentError) as exc:
        ContextRef.parse("@Event.DoesNotExist")(ctx)
    assert "DoesNotExist" in str(exc.value)
    assert "Event.DoesNotExist" in str(exc.value)


def test_resolve_value_literal_ref_and_callable(ctx):
    assert resolve_value("plain", ctx) == "plain"
    assert resolve_value(ContextRef.parse("@Workflow.ExternalId"), ctx) == "ext-42"
    assert resolve_value(lambda c: c.event.from_state, ctx) == "State1"
