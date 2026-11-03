"""Sorties mémoire de référence (tests et développement).

Portage de ``Outputs/Memories`` : stockage typé en mémoire, verrou par clé
CRC et les trois décorateurs de la chaîne standard
(``SetProperties → PushBus → PushModel``).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from .. import constants
from ..exceptions import LockFailedError
from ..models import RunContext
from ..values import resolve_value
from .base import LockObject, OutputAction

T = TypeVar("T")


class MemoryStorage:
    """Stockage en mémoire, indexé par type puis par clé UUID."""

    def __init__(self) -> None:
        self._items: Dict[type, Dict[UUID, Any]] = {}
        self._lock = threading.Lock()

    def save(self, key: UUID, item: Any) -> None:
        with self._lock:
            box = self._items.setdefault(type(item), {})
            box[key] = item

    def remove(self, item_type: type, key: UUID) -> None:
        with self._lock:
            box = self._items.get(item_type)
            if box is not None:
                box.pop(key, None)

    def get(self, item_type: Type[T], key: UUID) -> Optional[T]:
        box = self._items.get(item_type)
        return box.get(key) if box is not None else None

    def get_all(self, item_type: Type[T]) -> List[T]:
        box = self._items.get(item_type, {})
        return list(box.values())

    def get_by(self, item_type: Type[T], value: Any, attribute: str) -> List[T]:
        """Les éléments dont ``attribute`` vaut ``value`` (ex. ``external_id``)."""
        return [
            item
            for item in self.get_all(item_type)
            if getattr(item, attribute, None) == value
        ]


class MemoryLocker(LockObject):
    """Verrou mémoire par clé CRC, avec délai d'attente.

    Portage de ``LockerMemory`` : attente active (yield) jusqu'au délai,
    puis :class:`LockFailedError`.
    """

    def __init__(self, timeout: float = 3.0) -> None:
        self._timeout = timeout
        self._locked: Dict[int, float] = {}
        self._guard = threading.Lock()

    def lock(self, crc: int) -> None:
        deadline = time.monotonic() + self._timeout
        while True:
            with self._guard:
                if crc not in self._locked:
                    self._locked[crc] = time.monotonic()
                    return
            if time.monotonic() > deadline:
                raise LockFailedError(f"lock failed for key {crc}")
            time.sleep(0.001)

    def unlock(self, crc: int) -> None:
        with self._guard:
            self._locked.pop(crc, None)


class SetPropertiesOutputAction(OutputAction):
    """Applique les actions ``STORE`` (``$_update``) aux données du workflow.

    Le source passait par ``DynObject.Add`` dont les branches ``ContainsKey``
    étaient inversées (bug §5) — ici, simple affectation de dict.
    """

    def _prepare_impl(self, ctx: RunContext) -> None:
        for action in ctx.actions:
            if action.kind != constants.SET_VALUE_ACTION_NAME:
                continue
            key = str(resolve_value(action.arguments["key"], ctx))
            value = resolve_value(action.arguments["value"], ctx)
            ctx.workflow.extended_datas[key] = value

    def _execute_impl(self) -> None:
        pass


class PushBusOutputAction(OutputAction):
    """Pousse les actions matérialisées ``$_push`` vers le stockage mémoire.

    Portage de ``PushBusActionOutputActionInMemory`` (le « bus » des tests).
    """

    def __init__(self, storage: MemoryStorage, child: Optional[OutputAction] = None) -> None:
        super().__init__(child)
        self._storage = storage

    def _prepare_impl(self, ctx: RunContext) -> None:
        self.items.extend(
            action
            for action in ctx.event.actions
            if action.kind == constants.PUSH_ACTION_NAME
        )

    def _execute_impl(self) -> None:
        for item in self.items:
            self._storage.save(item.uuid, item)


class PushModelOutputAction(OutputAction):
    """Persiste le workflow (modèle) dans le stockage mémoire.

    Portage de ``PushModelOutputActionInMemory``.
    """

    def __init__(self, storage: MemoryStorage, child: Optional[OutputAction] = None) -> None:
        super().__init__(child)
        self._storage = storage

    def _prepare_impl(self, ctx: RunContext) -> None:
        self.items.append(ctx.workflow)

    def _execute_impl(self) -> None:
        for workflow in self.items:
            self._storage.save(workflow.uuid, workflow)


def default_memory_output(storage: MemoryStorage) -> Callable[[], OutputAction]:
    """Fabrique de la chaîne standard ``SetProperties → PushBus → PushModel``."""

    def create() -> OutputAction:
        return SetPropertiesOutputAction(
            PushBusOutputAction(storage, PushModelOutputAction(storage))
        )

    return create
