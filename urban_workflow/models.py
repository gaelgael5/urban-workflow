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
from typing import Any
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
    creation_date: datetime | None = None
    event_date: datetime | None = None
    #: Date d'insertion dans le système (``IntegrationDate``) : posée par le
    #: moteur à l'entrée de ``evaluate_event`` (horloge ``WorkflowClock``),
    #: jamais lue du payload — l'émetteur ne peut pas la fixer.
    integration_date: datetime | None = None
    #: Clé d'idempotence fournie par l'émetteur (propriété ``DedupKey``
    #: du payload) — prioritaire sur les clés ``UNIQUE`` du DSL.
    dedup_key: str = ""
    #: Vrai si ``uuid`` vient du payload, faux s'il a été généré par
    #: :func:`new_uuid`. Sans ce drapeau les deux cas seraient
    #: indiscernables (``uuid`` est toujours renseigné), et le repli
    #: anti-doublon automatique du moteur dédoublonnerait sur un Uuid
    #: tiré au hasard — donc jamais. Un appelant qui construit lui-même
    #: l'événement avec un Uuid porteur de sens le met à vrai.
    uuid_from_payload: bool = False
    extended_datas: dict[str, Any] = field(default_factory=dict)


@dataclass
class PushedAction:
    """Action matérialisée (message prêt à pousser) accrochée à un événement."""

    uuid: UUID = field(default_factory=new_uuid)
    name: str = ""
    kind: str = ""
    change: ChangeEnum = ChangeEnum.NONE
    execute_message: dict[str, Any] | None = None
    result_message: dict[str, Any] | None = None
    cancel_message: dict[str, Any] | None = None
    result_cancel_message: dict[str, Any] | None = None


@dataclass
class Event:
    """Événement intégré dans l'historique d'un workflow."""

    name: str = ""
    uuid: UUID = field(default_factory=new_uuid)
    creation_date: datetime | None = None
    event_date: datetime | None = None
    #: Date d'insertion dans le système, reprise de l'événement entrant.
    integration_date: datetime | None = None
    from_state: str = ""
    to_state: str = ""
    change: ChangeEnum = ChangeEnum.NONE
    #: Empreinte anti-doublon (SHA-256) de la clé retenue par
    #: ``WorkflowProcessor._event_gate`` : ``DedupKey`` émetteur, sinon
    #: propriétés ``UNIQUE`` déclarées, sinon repli sur le socle (``Uuid``
    #: du payload, ou ``Name`` + ``EventDate`` + ``ExternalId``). Vide
    #: seulement quand aucune clé ne s'applique (ni ``Uuid`` d'émetteur ni
    #: ``EventDate``).
    dedup_hash: str = ""
    actions: list[PushedAction] = field(default_factory=list)
    extended_datas: dict[str, Any] = field(default_factory=dict)

    def get_action(self, action_uuid: UUID) -> PushedAction | None:
        for action in self.actions:
            if action.uuid == action_uuid:
                return action
        return None

    def add_actions(self, *actions: PushedAction) -> Event:
        self.actions.extend(actions)
        return self


@dataclass
class StateInstance:
    """Instance d'état : créée à CHAQUE passage par un SWITCH.

    Socle non modifiable ``Name``/``Uuid``/``CreationDate`` (date d'entrée
    dans l'état)/``EventId`` (événement entrant qui l'a créé — c'est l'état
    qui référence l'événement, et non l'événement qui porte des états : un
    même événement peut être traité par plusieurs workflows) ;
    ``extended_datas`` portera les champs métier décrits par
    le schéma de l'état (``DEFINE STATE X … AS @schema``) — leur calcul
    reste à cadrer.
    """

    name: str = ""
    uuid: UUID = field(default_factory=new_uuid)
    creation_date: datetime | None = None
    event_id: UUID | None = None
    extended_datas: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """Instance de workflow : son identité et l'historique de ses événements."""

    workflow_name: str = ""
    version: int = 0
    uuid: UUID = field(default_factory=new_uuid)
    external_id: str = ""
    concurrency: int = 0
    creation_date: datetime | None = None
    last_update_date: datetime | None = None
    recursive: bool = False
    change: ChangeEnum = ChangeEnum.NONE
    events: list[Event] = field(default_factory=list)
    #: Historique des instances d'état, dans l'ordre des SWITCH.
    states: list[StateInstance] = field(default_factory=list)
    extended_datas: dict[str, Any] = field(default_factory=dict)

    @property
    def last_event(self) -> Event | None:
        return self.events[-1] if self.events else None

    @property
    def current_state(self) -> str:
        return self.events[-1].to_state if self.events else ""

    def get_event(self, event_uuid: UUID) -> Event | None:
        for event in self.events:
            if event.uuid == event_uuid:
                return event
        return None

    def add_events(self, *events: Event) -> Workflow:
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
    event: Event | None = None
    event_date: datetime | None = None
    arguments: dict[str, ContextValue] = field(default_factory=dict)

    def resolve_arguments(self, ctx: RunContext) -> dict[str, Any]:
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
    def none(cls) -> RuleSpan:
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

    workflow: Workflow | None = None
    incoming_event: IncomingEvent | None = None
    event: Event | None = None
    extended_datas: dict[str, Any] = field(default_factory=dict)
    actions: list[ResultAction] = field(default_factory=list)
    functional_log: list[str] = field(default_factory=list)
    current_evaluation: CurrentEvaluation = field(default_factory=CurrentEvaluation)
    #: Instances d'état créées par les SWITCH de cette évaluation, versées
    #: dans ``workflow.states`` à l'ajout de l'événement à l'historique.
    #: Créées dès le SWITCH (et non à l'ajout) : les règles de l'état cible
    #: évaluées dans la foulée (RECURSIVE) voient déjà ``@state.Uuid``.
    pending_states: list[StateInstance] = field(default_factory=list)
