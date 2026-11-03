"""Modèles d'exécution du moteur.

Portage des classes de ``Bb.Workflows.Models`` en dataclasses. Les
``DynObject`` du source (arbres JSON paresseux) deviennent de simples
dictionnaires JSON-compatibles ; les valeurs paresseuses des arguments
d'action vivent dans :mod:`urban_workflow.values`.
"""

from __future__ import annotations

import enum
import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .values import ContextValue, resolve_value


class ChangeEnum(enum.Enum):
    NONE = "None"
    NEW = "New"
    UPDATED = "Updated"


def new_uuid() -> UUID:
    return uuid_module.uuid4()


@dataclass
class IncomingEvent:
    """Événement entrant, désérialisé depuis un payload externe."""

    name: str = ""
    uuid: UUID = field(default_factory=new_uuid)
    external_id: str = ""
    creation_date: Optional[datetime] = None
    event_date: Optional[datetime] = None
    extended_datas: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PushedAction:
    """Action matérialisée (message prêt à pousser) accrochée à un événement."""

    uuid: UUID = field(default_factory=new_uuid)
    name: str = ""
    kind: str = ""
    change: ChangeEnum = ChangeEnum.NONE
    execute_message: Optional[Dict[str, Any]] = None
    result_message: Optional[Dict[str, Any]] = None
    cancel_message: Optional[Dict[str, Any]] = None
    result_cancel_message: Optional[Dict[str, Any]] = None


@dataclass
class Event:
    """Événement intégré dans l'historique d'un workflow."""

    name: str = ""
    uuid: UUID = field(default_factory=new_uuid)
    creation_date: Optional[datetime] = None
    event_date: Optional[datetime] = None
    from_state: str = ""
    to_state: str = ""
    change: ChangeEnum = ChangeEnum.NONE
    actions: List[PushedAction] = field(default_factory=list)
    extended_datas: Dict[str, Any] = field(default_factory=dict)

    def get_action(self, action_uuid: UUID) -> Optional[PushedAction]:
        for action in self.actions:
            if action.uuid == action_uuid:
                return action
        return None

    def add_actions(self, *actions: PushedAction) -> "Event":
        self.actions.extend(actions)
        return self


@dataclass
class Workflow:
    """Instance de workflow : son identité et l'historique de ses événements."""

    workflow_name: str = ""
    version: int = 0
    uuid: UUID = field(default_factory=new_uuid)
    external_id: str = ""
    concurrency: int = 0
    creation_date: Optional[datetime] = None
    last_update_date: Optional[datetime] = None
    recursive: bool = False
    change: ChangeEnum = ChangeEnum.NONE
    events: List[Event] = field(default_factory=list)
    extended_datas: Dict[str, Any] = field(default_factory=dict)

    @property
    def last_event(self) -> Optional[Event]:
        return self.events[-1] if self.events else None

    @property
    def current_state(self) -> str:
        return self.events[-1].to_state if self.events else ""

    def get_event(self, event_uuid: UUID) -> Optional[Event]:
        for event in self.events:
            if event.uuid == event_uuid:
                return event
        return None

    def add_events(self, *events: Event) -> "Workflow":
        self.events.extend(events)
        return self


@dataclass
class ResultAction:
    """Action collectée pendant l'évaluation, avant matérialisation.

    ``arguments`` conserve les valeurs **non résolues** (littéraux,
    :class:`~urban_workflow.values.ContextRef`, callables) — la résolution
    a lieu au moment de la traduction en message, comme dans le source.
    """

    name: str = ""
    uuid: UUID = field(default_factory=new_uuid)
    label: str = ""
    delay: int = 0
    kind: str = ""
    event: Optional[Event] = None
    event_date: Optional[datetime] = None
    arguments: Dict[str, ContextValue] = field(default_factory=dict)

    def resolve_arguments(self, ctx: "RunContext") -> Dict[str, Any]:
        """Résout tous les arguments contre le contexte d'exécution."""
        return {key: resolve_value(value, ctx) for key, value in self.arguments.items()}


@dataclass
class RuleSpan:
    """Position d'une règle dans le script DSL source (diagnostics)."""

    start_line: int = 0
    start_column: int = 0
    start_index: int = 0
    stop_line: int = 0
    stop_column: int = 0
    stop_index: int = 0

    @classmethod
    def none(cls) -> "RuleSpan":
        return _RULE_SPAN_NONE


_RULE_SPAN_NONE = RuleSpan()


@dataclass
class CurrentEvaluation:
    """Trace de la règle ``WHEN`` en cours d'évaluation (diagnostics)."""

    when_rule_text: str = ""
    when_rule_code: str = ""
    when_rule_position: RuleSpan = field(default_factory=RuleSpan.none)

    def clear(self) -> None:
        self.when_rule_text = ""
        self.when_rule_code = ""
        self.when_rule_position = RuleSpan.none()


@dataclass
class RunContext:
    """Contexte d'évaluation d'un événement sur un workflow.

    C'est l'objet passé aux règles et actions métier. Les chemins du DSL
    (``@Event.ExternalId``, ``@Workflow.Uuid``…) se résolvent dessus via
    :class:`~urban_workflow.values.ContextRef`.
    """

    workflow: Optional[Workflow] = None
    incoming_event: Optional[IncomingEvent] = None
    event: Optional[Event] = None
    extended_datas: Dict[str, Any] = field(default_factory=dict)
    actions: List[ResultAction] = field(default_factory=list)
    functional_log: List[str] = field(default_factory=list)
    current_evaluation: CurrentEvaluation = field(default_factory=CurrentEvaluation)
