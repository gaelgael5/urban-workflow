"""Chaîne de sorties (décorateur) et transactions.

Portage de ``OutputAction`` / ``ITransaction`` / ``BaseTransaction``.

Différence assumée avec le source : ``BaseTransaction.Dispose`` ne
déclenchait le rollback que si la transaction avait *déjà* été annulée
(``!commited && roolbacked`` — condition inversée, le rollback automatique
ne se produisait jamais). Ici, :class:`Transaction` est un gestionnaire de
contexte qui annule réellement la transaction si le bloc sort sans
``commit()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import RunContext


class Transaction(ABC):
    """Transaction chaînée (chaque maillon de la chaîne de sorties a la sienne)."""

    def __init__(self) -> None:
        self.child: Transaction | None = None
        self._committed = False
        self._rolled_back = False

    @property
    def committed(self) -> bool:
        return self._committed

    @property
    def rolled_back(self) -> bool:
        return self._rolled_back

    def commit(self) -> None:
        self._commit_impl()
        if self.child is not None:
            self.child.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._rolled_back:
            return
        self._rolled_back = True
        self._rollback_impl()
        if self.child is not None:
            self.child.rollback()

    @abstractmethod
    def _commit_impl(self) -> None: ...

    @abstractmethod
    def _rollback_impl(self) -> None: ...

    # ------------------------------------------------------------------
    # Gestionnaire de contexte : rollback si le bloc sort sans commit.
    # ------------------------------------------------------------------

    def __enter__(self) -> Transaction:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._committed:
            self.rollback()


class DoNothingTransaction(Transaction):
    """Transaction vide (sorties sans état transactionnel)."""

    def _commit_impl(self) -> None:
        pass

    def _rollback_impl(self) -> None:
        pass


class OutputAction(ABC):
    """Maillon de la chaîne de sorties (pattern décorateur).

    Cycle : ``prepare(ctx)`` pour chaque contexte évalué, puis
    ``begin_transaction()`` et ``execute()`` sous transaction.
    """

    def __init__(self, child: OutputAction | None = None) -> None:
        self._child = child
        self.items: list[Any] = []

    @property
    def child(self) -> OutputAction | None:
        return self._child

    def prepare(self, ctx: RunContext) -> None:
        self._prepare_impl(ctx)
        if self._child is not None:
            self._child.prepare(ctx)

    def execute(self) -> None:
        self._execute_impl()
        if self._child is not None:
            self._child.execute()

    def begin_transaction(self) -> Transaction:
        transaction = self._begin_transaction_impl()
        if self._child is not None:
            transaction.child = self._child.begin_transaction()
        return transaction

    @abstractmethod
    def _prepare_impl(self, ctx: RunContext) -> None: ...

    @abstractmethod
    def _execute_impl(self) -> None: ...

    def _begin_transaction_impl(self) -> Transaction:
        return DoNothingTransaction()


class LockObject(ABC):
    """Verrou par clé CRC (portage de ``ILockObject``)."""

    @abstractmethod
    def lock(self, crc: int) -> None: ...

    @abstractmethod
    def unlock(self, crc: int) -> None: ...


class OutputBus(ABC):
    """Bus de sortie des actions matérialisées (contrat ``Outputs.Mom``).

    Interface abstraite seulement en v1 : les implémentations concrètes
    (RabbitMQ, Kafka, outbox…) vivent hors du cœur. À brancher dans la
    chaîne de sorties via :class:`BusOutputAction`.
    """

    @abstractmethod
    def push(self, action) -> None:
        """Pousse une :class:`~urban_workflow.models.PushedAction`."""


class BusOutputAction(OutputAction):
    """Maillon générique : pousse les actions d'un ``kind`` donné vers un bus."""

    def __init__(
        self,
        bus: OutputBus,
        kinds: tuple = ("$_push",),
        child: OutputAction | None = None,
    ) -> None:
        super().__init__(child)
        self._bus = bus
        self._kinds = tuple(kinds)

    def _prepare_impl(self, ctx: RunContext) -> None:
        self.items.extend(
            action for action in ctx.event.actions if action.kind in self._kinds
        )

    def _execute_impl(self) -> None:
        for action in self.items:
            self._bus.push(action)
