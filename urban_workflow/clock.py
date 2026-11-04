"""Horloge du moteur, injectable pour les tests.

Portage de ``WorkflowClock`` : tout le moteur date ses objets via
``WorkflowClock.now()`` et jamais via ``datetime.now`` directement, ce qui
permet de figer le temps dans les tests (expirations, rappels différés).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone


def _default_provider() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowClock:
    """Source de temps unique du moteur (UTC, avec fuseau)."""

    _provider: Callable[[], datetime] = staticmethod(_default_provider)

    @classmethod
    def now(cls) -> datetime:
        return cls._provider()

    @classmethod
    def set_provider(cls, provider: Callable[[], datetime]) -> None:
        cls._provider = staticmethod(provider)

    @classmethod
    def reset(cls) -> None:
        cls._provider = staticmethod(_default_provider)

    @classmethod
    @contextmanager
    def frozen(cls, instant: datetime) -> Iterator[datetime]:
        """Fige l'horloge sur ``instant`` le temps du bloc ``with``."""
        previous = cls._provider
        cls._provider = staticmethod(lambda: instant)
        try:
            yield instant
        finally:
            cls._provider = previous
