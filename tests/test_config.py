"""Tests du modèle de configuration et des builders fluides.

La configuration construite ici reprend celle de ``WorkflowsUnitTest``
du projet source (``InitializeWorkflow``) : construction à la main, sans
DSL — le moteur viendra l'exécuter à l'étape suivante.
"""

import pytest

from urban_workflow import (
    IncomingEvent,
    IncomingEventConfig,
    InitializationOnEventConfig,
    MissingConfigurationError,
    MissingStateError,
    ResultActionConfig,
    RunContext,
    StateConfig,
    TransitionConfig,
    Workflow,
    WorkflowConfig,
    WorkflowsConfig,
    constants,
)
from urban_workflow.values import ContextRef


def build_wrk1(version: int = 1) -> WorkflowConfig:
    """La config du test source InitializeWorkflow."""
    return (
        WorkflowConfig(name="wrk1", label="wrk1 config", version=version)
        .add_initializer(
            InitializationOnEventConfig(event_name="evnt1", recursive=True).add_switch("State1")
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


def test_build_resolves_target_states():
    config = build_wrk1().build()

    switch = config.initializers["evnt1"].switchs[0]
    assert switch.target_state is config.states["State1"]

    transition = config.states["State1"].events["evnt1"].transitions[0]
    assert transition.target_state is config.states["State2"]
    assert transition.label == "State1 -> State2"


def test_build_declares_events_automatically():
    config = build_wrk1().build()
    # $_result (technique), evnt1 (initialiseur + état)
    assert constants.RESULT_ACTION_NAME in config.declared_events
    assert "evnt1" in config.declared_events
    assert config.declared_events[constants.RESULT_ACTION_NAME].label != ""


def test_build_missing_state_raises():
    config = WorkflowConfig(name="bad", version=1).add_initializer(
        InitializationOnEventConfig(event_name="e").add_switch("Nowhere")
    )
    with pytest.raises(MissingStateError) as exc:
        config.build()
    assert "Nowhere" in str(exc.value)


def test_build_is_idempotent():
    config = build_wrk1()
    config.build()
    config.build()  # ne doit pas re-déclarer ni échouer
    assert len(config.declared_events) == 2


def test_evaluate_filter_matching():
    config = build_wrk1()
    config.add_filter("Country", "France")

    event_fr = IncomingEvent(name="evnt1")
    event_fr.extended_datas["Country"] = "France"
    event_de = IncomingEvent(name="evnt1")
    event_de.extended_datas["Country"] = "Germany"
    event_none = IncomingEvent(name="evnt1")

    assert config.evaluate_filter(event_fr) is True
    assert config.evaluate_filter(event_de) is False
    assert config.evaluate_filter(event_none) is False


def test_workflows_config_get_by_name_and_version():
    configs = WorkflowsConfig()
    configs.add_document(build_wrk1(version=1))
    configs.add_document(build_wrk1(version=2))

    assert configs.get("wrk1", 2).version == 2
    assert len(configs.get_all("wrk1")) == 2
    with pytest.raises(MissingConfigurationError):
        configs.get("wrk1", 99)
    with pytest.raises(MissingConfigurationError):
        configs.get("unknown", 1)


def test_workflows_config_matching_honors_filters_and_version_selector():
    configs = WorkflowsConfig()
    configs.add_document(build_wrk1(version=1))
    configs.add_document(build_wrk1(version=2))

    event = IncomingEvent(name="evnt1")
    assert {c.version for c in configs.matching(event)} == {1, 2}

    # Restreint la création aux workflows version 2.
    configs.set_version_selector("wrk1", 2)
    assert {c.version for c in configs.matching(event)} == {2}


def test_result_action_config_map_and_arguments():
    action_config = (
        ResultActionConfig(name="Cut", kind=constants.PUSH_ACTION_NAME)
        .add_argument("key", "@IncomingEvent.ExternalId")
        .add_argument("mode", "hard")
    )
    assert isinstance(action_config.arguments["key"], ContextRef)

    incoming = IncomingEvent(name="evnt1", external_id="ext-7")
    ctx = RunContext(workflow=Workflow(), incoming_event=incoming)

    action = action_config.map(ctx)
    assert action.name == "Cut"
    assert action.kind == constants.PUSH_ACTION_NAME
    assert action.event_date is not None
    # Les arguments restent paresseux jusqu'à la résolution explicite.
    assert action.resolve_arguments(ctx) == {"key": "ext-7", "mode": "hard"}


def test_rule_actions_grouped_by_shared_rule():
    def always(ctx):
        return True

    state = StateConfig(name="S")
    state.add_incoming_actions(always, ResultActionConfig(name="A"))
    state.add_incoming_actions(always, ResultActionConfig(name="B"))
    state.add_incoming_actions(None, ResultActionConfig(name="C"))

    assert len(state.incoming_rules) == 2  # 'always' regroupé, None séparé
    grouped = next(r for r in state.incoming_rules if r.when_rule is always)
    assert [a.name for a in grouped.actions] == ["A", "B"]
