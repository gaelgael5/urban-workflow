"""Sorties du moteur : chaîne de décorateurs ``OutputAction`` + transactions.

Portage de ``Bb.Workflows.Outputs`` — le pattern décorateur + transaction du
source est conservé ; ``MemoryStorage`` sert de stockage de référence pour
les tests.
"""

from .base import (
    BusOutputAction,
    DoNothingTransaction,
    LockObject,
    OutputAction,
    OutputBus,
    Transaction,
)
from .memory import (
    MemoryLocker,
    MemoryStorage,
    PushBusOutputAction,
    PushModelOutputAction,
    SetPropertiesOutputAction,
    default_memory_output,
)

__all__ = [
    "BusOutputAction",
    "DoNothingTransaction",
    "LockObject",
    "OutputBus",
    "MemoryLocker",
    "MemoryStorage",
    "OutputAction",
    "PushBusOutputAction",
    "PushModelOutputAction",
    "SetPropertiesOutputAction",
    "Transaction",
    "default_memory_output",
]
