"""Chaîne de sorties SQL : persistance sous transaction réelle.

Tous les maillons SQL d'une même chaîne partagent une unité de travail
(:class:`SqlUnitOfWork`) : une seule connexion, une seule transaction —
commit si toute la chaîne réussit, rollback sinon (le moteur annule la
transaction et laisse l'exception remonter ; l'événement est rejouable
sans doublon).
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.engine import Connection

from ..models import RunContext, Workflow
from ..outputs.base import BusOutputAction, OutputAction, OutputBus, Transaction
from ..outputs.memory import SetPropertiesOutputAction
from .storage import SqlWorkflowStorage


class SqlUnitOfWork:
    """Connexion + transaction partagées par les maillons SQL d'une chaîne."""

    def __init__(self, storage: SqlWorkflowStorage) -> None:
        self._storage = storage
        self._connection: Connection | None = None
        self._transaction = None
        self._finished = False

    def connection(self) -> Connection:
        if self._connection is None:
            self._connection = self._storage.engine.connect()
            self._transaction = self._connection.begin()
        return self._connection

    def commit(self) -> None:
        self._finish("commit")

    def rollback(self) -> None:
        self._finish("rollback")

    def _finish(self, how: str) -> None:
        if self._finished:
            return
        self._finished = True
        if self._transaction is not None:
            getattr(self._transaction, how)()
        if self._connection is not None:
            self._connection.close()


class SqlTransaction(Transaction):
    """Transaction de maillon déléguée à l'unité de travail partagée."""

    def __init__(self, unit_of_work: SqlUnitOfWork) -> None:
        super().__init__()
        self._unit_of_work = unit_of_work

    def _commit_impl(self) -> None:
        self._unit_of_work.commit()

    def _rollback_impl(self) -> None:
        self._unit_of_work.rollback()


class SqlPushModelOutputAction(OutputAction):
    """Persiste les workflows impactés (équivalent SQL de ``PushModel``).

    Les actions matérialisées sont persistées avec l'agrégat
    (table ``workflow_actions``, messages inclus) : c'est l'outbox.
    """

    def __init__(
        self,
        storage: SqlWorkflowStorage,
        unit_of_work: SqlUnitOfWork,
        child: OutputAction | None = None,
    ) -> None:
        super().__init__(child)
        self._storage = storage
        self._unit_of_work = unit_of_work

    def _prepare_impl(self, ctx: RunContext) -> None:
        self.items.append(ctx.workflow)

    def _execute_impl(self) -> None:
        connection = self._unit_of_work.connection()
        for workflow in self.items:
            if isinstance(workflow, Workflow):
                self._storage.save_workflow(workflow, connection=connection)

    def _begin_transaction_impl(self) -> Transaction:
        return SqlTransaction(self._unit_of_work)


def sql_output(
    storage: SqlWorkflowStorage, bus: OutputBus | None = None
) -> Callable[[], OutputAction]:
    """Fabrique de la chaîne SQL standard.

    ``SetProperties → (bus ?) → SqlPushModel`` — même ordre que la chaîne
    mémoire. Chaque évaluation reçoit une chaîne et une unité de travail
    neuves.
    """

    def create() -> OutputAction:
        unit_of_work = SqlUnitOfWork(storage)
        tail: OutputAction = SqlPushModelOutputAction(storage, unit_of_work)
        if bus is not None:
            tail = BusOutputAction(bus, child=tail)
        return SetPropertiesOutputAction(tail)

    return create
