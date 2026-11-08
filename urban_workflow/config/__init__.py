"""Modèle de configuration des workflows (cible du visiteur DSL)."""

from .rules import (
    DeclaredArtifactConfig,
    DeclaredEventConfig,
    ResultActionConfig,
    ResultRuleConfig,
    Rule,
    append_rule_actions,
)
from .states import (
    IncomingEventConfig,
    InitializationConfig,
    InitializationOnEventConfig,
    StateConfig,
    TransitionConfig,
)
from .workflow import WorkflowConfig, WorkflowsConfig

__all__ = [
    "DeclaredArtifactConfig",
    "DeclaredEventConfig",
    "IncomingEventConfig",
    "InitializationConfig",
    "InitializationOnEventConfig",
    "ResultActionConfig",
    "ResultRuleConfig",
    "Rule",
    "StateConfig",
    "TransitionConfig",
    "WorkflowConfig",
    "WorkflowsConfig",
    "append_rule_actions",
]
