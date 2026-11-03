"""Point d'entrée du moteur (portage de ``WorkflowEngine``).

Sérialise l'évaluation des événements d'un même contexte : la clé de
verrouillage (``ExternalId`` par défaut) est hachée en CRC32
(``zlib.crc32``, comme le ``Crc2`` maison du source) et verrouillée le
temps du traitement.

Différence assumée avec le source (bug §5 non reproduit) :
``UseResource.Decrement`` appelait ``Interlocked.Increment`` — le compteur
d'utilisation ne redescendait jamais et ``CanBeRemoved`` restait faux.
Ici, le compteur décrémente réellement.
"""

from __future__ import annotations

import threading
import zlib
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any

from ..exceptions import InvalidIncomingEventFormatError
from ..models import IncomingEvent, RunContext
from ..outputs.base import LockObject
from ..outputs.memory import MemoryLocker
from .processor import WorkflowProcessor


class WorkflowEngine:
    """Évalue des payloads d'événements sous verrou par ``ExternalId``."""

    def __init__(
        self,
        processor: WorkflowProcessor,
        *,
        locker: LockObject | None = None,
        thread_safe_key: Callable[[IncomingEvent], str] | None = None,
    ) -> None:
        self.processor = processor
        self.locker = locker if locker is not None else MemoryLocker()
        #: Clé de sérialisation des traitements (``ExternalId`` par défaut).
        self.thread_safe_key = thread_safe_key or (lambda event: event.external_id)

        self._use_count = 0
        self._use_guard = threading.Lock()

    def evaluate_event(
        self,
        payload: str | Mapping[str, Any] | IncomingEvent,
        incoming_type: str | None = None,
    ) -> list[RunContext]:
        """Désérialise ``payload`` puis l'évalue sous verrou.

        Accepte un JSON (chaîne), un mapping déjà désérialisé ou un
        :class:`IncomingEvent` construit par l'appelant.
        """
        try:
            event = self.processor.factory.create_base_incoming_event(
                payload, incoming_type
            )
        except Exception as exc:
            raise InvalidIncomingEventFormatError("Invalid format") from exc

        key = str(self.thread_safe_key(event))
        crc = zlib.crc32(key.encode("utf-8"))

        with self._locked(crc):
            return self.processor.evaluate_event(event)

    @property
    def can_be_removed(self) -> bool:
        """Vrai si aucune évaluation n'est en cours."""
        with self._use_guard:
            return self._use_count == 0

    @contextmanager
    def _locked(self, crc: int) -> Iterator[None]:
        self.locker.lock(crc)
        with self._use_guard:
            self._use_count += 1
        try:
            yield
        finally:
            self.locker.unlock(crc)
            with self._use_guard:
                self._use_count -= 1
