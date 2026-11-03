"""urban-workflow — moteur de workflow piloté par un DSL métier.

Portage Python de `Black-Beard-Sdk/Workflow
<https://github.com/Black-Beard-Sdk/Workflow>`_, avec normalisation des
sorties JSON par `urban-json <https://pypi.org/project/urban-json/>`_.
"""

from .clock import WorkflowClock
from .engine import (
    ActionTranslator,
    DefaultActionTranslator,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    parse_incoming_event,
)
from .outputs import (
    DoNothingTransaction,
    LockObject,
    MemoryLocker,
    MemoryStorage,
    OutputAction,
    PushBusOutputAction,
    PushModelOutputAction,
    SetPropertiesOutputAction,
    Transaction,
)
from .config import (
    DeclaredEventConfig,
    IncomingEventConfig,
    InitializationConfig,
    InitializationOnEventConfig,
    ResultActionConfig,
    ResultRuleConfig,
    StateConfig,
    TransitionConfig,
    WorkflowConfig,
    WorkflowsConfig,
)
from .exceptions import (
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidIncomingEventFormatError,
    InvalidMethodReferenceError,
    LockFailedError,
    MissingArgumentNameError,
    MissingConfigurationError,
    MissingStateError,
    ResolutionArgumentError,
    WorkflowError,
)
from .models import (
    ChangeEnum,
    CurrentEvaluation,
    Event,
    IncomingEvent,
    PushedAction,
    ResultAction,
    RuleSpan,
    RunContext,
    Workflow,
)
from .registry import FunctionRegistry
from .values import ContextRef, make_value, resolve_value

__version__ = "0.1.0"

__all__ = [
    "ActionTranslator",
    "ChangeEnum",
    "ContextRef",
    "CurrentEvaluation",
    "DefaultActionTranslator",
    "DoNothingTransaction",
    "LockObject",
    "MemoryLocker",
    "MemoryStorage",
    "OutputAction",
    "PushBusOutputAction",
    "PushModelOutputAction",
    "SetPropertiesOutputAction",
    "Transaction",
    "WorkflowEngine",
    "WorkflowFactory",
    "WorkflowProcessor",
    "parse_incoming_event",
    "DeclaredEventConfig",
    "DuplicatedArgumentNameError",
    "Event",
    "FunctionRegistry",
    "IncomingEvent",
    "IncomingEventConfig",
    "InitializationConfig",
    "InitializationOnEventConfig",
    "InvalidArgumentNameError",
    "InvalidIncomingEventFormatError",
    "InvalidMethodReferenceError",
    "LockFailedError",
    "MissingArgumentNameError",
    "MissingConfigurationError",
    "MissingStateError",
    "PushedAction",
    "ResolutionArgumentError",
    "ResultAction",
    "ResultActionConfig",
    "ResultRuleConfig",
    "RuleSpan",
    "RunContext",
    "StateConfig",
    "TransitionConfig",
    "Workflow",
    "WorkflowClock",
    "WorkflowConfig",
    "WorkflowError",
    "WorkflowsConfig",
    "make_value",
    "resolve_value",
]
