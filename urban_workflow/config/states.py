"""Configuration des états, transitions et initialisations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import RuleSpan
from .rules import ResultActionConfig, ResultRuleConfig, Rule, append_rule_actions


@dataclass
class TransitionConfig:
    """``(WHEN règle)? … SWITCH état`` au sein d'un ``ON EVENT``."""

    target_state_name: str = ""
    when_rule: Rule | None = None
    when_rule_text: str = ""
    when_rule_code: str = ""
    when_rule_position: RuleSpan = field(default_factory=RuleSpan.none)
    rule_actions: list[ResultRuleConfig] = field(default_factory=list)

    #: Résolu par :meth:`WorkflowConfig.build`.
    target_state: StateConfig | None = None
    label: str = ""

    def add_actions(
        self, when_rule: Rule | None, *actions: ResultActionConfig
    ) -> TransitionConfig:
        append_rule_actions(self.rule_actions, when_rule, *actions)
        return self


@dataclass
class IncomingEventConfig:
    """``ON EVENT nom`` d'un état : règles exécutées et transitions."""

    name: str = ""
    transitions: list[TransitionConfig] = field(default_factory=list)
    rules: list[ResultRuleConfig] = field(default_factory=list)

    def add_transition(self, transition: TransitionConfig) -> IncomingEventConfig:
        self.transitions.append(transition)
        return self

    def add_action(
        self, when_rule: Rule | None, action: ResultActionConfig
    ) -> IncomingEventConfig:
        append_rule_actions(self.rules, when_rule, action)
        return self


@dataclass
class StateConfig:
    """``DEFINE STATE`` : événements écoutés et règles d'entrée/sortie."""

    name: str = ""
    label: str = ""
    #: Nom donné après ``AS @…`` (schéma des champs métier de l'état) ;
    #: ``schema`` est résolu quand un registre est fourni au visiteur.
    schema_ref: str = ""
    schema: dict[str, Any] | None = None
    events: dict[str, IncomingEventConfig] = field(default_factory=dict)
    incoming_rules: list[ResultRuleConfig] = field(default_factory=list)
    outcoming_rules: list[ResultRuleConfig] = field(default_factory=list)

    def add_event(self, event: IncomingEventConfig) -> StateConfig:
        self.events[event.name] = event
        return self

    def add_incoming_actions(
        self, when_rule: Rule | None, *actions: ResultActionConfig
    ) -> StateConfig:
        append_rule_actions(self.incoming_rules, when_rule, *actions)
        return self

    def add_outcoming_actions(
        self, when_rule: Rule | None, *actions: ResultActionConfig
    ) -> StateConfig:
        append_rule_actions(self.outcoming_rules, when_rule, *actions)
        return self


@dataclass
class InitializationConfig:
    """Un ``SWITCH`` d'initialisation : ``(WHEN règle)? SWITCH état``."""

    target_state_name: str = ""
    when_rule: Rule | None = None
    when_rule_text: str = ""
    when_rule_code: str = ""
    when_rule_position: RuleSpan = field(default_factory=RuleSpan.none)

    #: Résolu par :meth:`WorkflowConfig.build`.
    target_state: StateConfig | None = None


@dataclass
class InitializationOnEventConfig:
    """``INITIALIZE WORKFLOW ON EVENT nom`` : création de workflow."""

    event_name: str = ""
    recursive: bool = False
    switchs: list[InitializationConfig] = field(default_factory=list)

    def add_switch(
        self,
        target_state_name: str,
        when_rule: Rule | None = None,
        when_rule_text: str = "",
        when_rule_code: str = "",
        when_rule_position: RuleSpan | None = None,
    ) -> InitializationOnEventConfig:
        self.switchs.append(
            InitializationConfig(
                target_state_name=target_state_name,
                when_rule=when_rule,
                when_rule_text=when_rule_text,
                when_rule_code=when_rule_code,
                when_rule_position=when_rule_position or RuleSpan.none(),
            )
        )
        return self
