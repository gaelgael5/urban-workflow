"""Configuration d'un workflow et collection multi-configurations."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import dataclass, field

from .. import constants
from ..exceptions import MissingConfigurationError, MissingStateError
from ..models import IncomingEvent
from .rules import DeclaredEventConfig
from .states import InitializationOnEventConfig, StateConfig

_TECHNICAL_EVENT_LABELS = {
    constants.RESULT_ACTION_NAME: (
        "technical result of execution of an order pushed by the current workflow"
    ),
    constants.EXPIRED_EVENT_NAME: "Expiration of the state",
}


@dataclass
class WorkflowConfig:
    """Machine à états déclarée (une version d'un workflow)."""

    name: str = ""
    label: str = ""
    version: int = 0
    concurrency: int = 1
    crc: int = 0
    filters: dict[str, str] = field(default_factory=dict)
    initializers: dict[str, InitializationOnEventConfig] = field(default_factory=dict)
    declared_events: dict[str, DeclaredEventConfig] = field(default_factory=dict)
    states: dict[str, StateConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._built = False
        self._build_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Construction fluide
    # ------------------------------------------------------------------

    def add_state(self, state: StateConfig) -> WorkflowConfig:
        self.states[state.name] = state
        return self

    def add_initializer(self, initializer: InitializationOnEventConfig) -> WorkflowConfig:
        self.initializers[initializer.event_name] = initializer
        return self

    def add_filter(self, key: str, value: str) -> WorkflowConfig:
        """``MATCHING (key = 'value')`` : filtre de routage des événements."""
        self.filters[key] = value
        return self

    # ------------------------------------------------------------------
    # Construction / résolution
    # ------------------------------------------------------------------

    def build(self) -> WorkflowConfig:
        """Résout les références et prépare la configuration (idempotent)."""
        if self._built:
            return self
        with self._build_lock:
            if self._built:
                return self
            self._build_declared_events()
            self._resolve_target_states()
            self._build_transition_labels()
            self._built = True
        return self

    def _build_declared_events(self) -> None:
        def declare(name: str) -> None:
            if name not in self.declared_events:
                self.declared_events[name] = DeclaredEventConfig(
                    name=name,
                    label=_TECHNICAL_EVENT_LABELS.get(name, ""),
                )

        declare(constants.RESULT_ACTION_NAME)

        for event_name in self.initializers:
            declare(event_name)

        for state in self.states.values():
            for event_name in state.events:
                declare(event_name)

    def _resolve_target_states(self) -> None:
        def resolve(target_state_name: str) -> StateConfig:
            state = self.states.get(target_state_name)
            if state is None:
                raise MissingStateError(f"missing state name {target_state_name}")
            return state

        for initializer in self.initializers.values():
            for switch in initializer.switchs:
                switch.target_state = resolve(switch.target_state_name)

        for state in self.states.values():
            for event in state.events.values():
                for transition in event.transitions:
                    transition.target_state = resolve(transition.target_state_name)

    def _build_transition_labels(self) -> None:
        for state_name, state in self.states.items():
            for event in state.events.values():
                for transition in event.transitions:
                    transition.label = f"{state_name} -> {transition.target_state_name}"

    # ------------------------------------------------------------------
    # Routage
    # ------------------------------------------------------------------

    def evaluate_filter(self, event: IncomingEvent) -> bool:
        """Vrai si les données étendues de l'événement satisfont ``MATCHING``."""
        self.build()
        for key, expected in self.filters.items():
            actual = event.extended_datas.get(key)
            if actual is None or str(actual) != expected:
                return False
        return True


class WorkflowsConfig:
    """Ensemble des configurations chargées dans le processeur.

    Gère le versionnage (plusieurs versions d'un même workflow) et le
    routage d'un événement vers les configurations dont les filtres
    ``MATCHING`` correspondent.
    """

    def __init__(self) -> None:
        self._configs: list[WorkflowConfig] = []
        self._by_name_version: dict[tuple[str, int], WorkflowConfig] = {}
        self._selectable: list[WorkflowConfig] = []
        self._version_selectors: dict[str, set[int]] = {}
        self._lock = threading.Lock()

    def set_version_selector(self, workflow_name: str, version: int) -> WorkflowsConfig:
        """Restreint la création de nouveaux workflows ``workflow_name`` à ``version``.

        Sans sélecteur, toutes les versions chargées sont candidates ; les
        workflows déjà créés continuent, eux, d'utiliser leur version d'origine.
        """
        with self._lock:
            self._version_selectors.setdefault(workflow_name, set()).add(version)
            self._rebuild_selectable()
        return self

    def add_document(self, config: WorkflowConfig) -> WorkflowsConfig:
        config.build()
        with self._lock:
            self._configs.append(config)
            self._by_name_version[(config.name, config.version)] = config
            self._rebuild_selectable()
        return self

    def _rebuild_selectable(self) -> None:
        self._selectable = [
            config
            for config in self._configs
            if config.name not in self._version_selectors
            or config.version in self._version_selectors[config.name]
        ]

    def matching(self, event: IncomingEvent) -> Iterator[WorkflowConfig]:
        """Configurations candidates pour un événement entrant."""
        for config in self._selectable:
            if config.evaluate_filter(event):
                yield config

    def get(self, workflow_name: str, version: int) -> WorkflowConfig:
        config = self._by_name_version.get((workflow_name, version))
        if config is None:
            raise MissingConfigurationError(f"{workflow_name} V {version}")
        return config

    def try_get(self, workflow_name: str, version: int) -> WorkflowConfig | None:
        return self._by_name_version.get((workflow_name, version))

    def get_all(self, workflow_name: str) -> list[WorkflowConfig]:
        return [config for config in self._configs if config.name == workflow_name]

    def __len__(self) -> int:
        return len(self._configs)
