"""Langage d'expressions des règles écrites dans le DSL.

``DEFINE RULE MontantEleve (DECIMAL seuil) 'montant élevé'
    AS @IncomingEvent.Montant > seuil;``

Extension urban-workflow (décision utilisateur du 2026-11-05) : une règle
peut porter son corps dans le DSL au lieu d'être une fonction enregistrée
dans le ``FunctionRegistry`` ; les deux coexistent avec la même syntaxe
d'appel (``WHEN MontantEleve(seuil = '1000')``).

Choix de sémantique — une règle ne doit JAMAIS faire tomber le traitement
d'un événement pour une donnée imprévue :

- une valeur absente vaut ``NULL`` (``None``) ; ``IS NULL`` la teste ;
- une comparaison d'ordre impossible (``NULL``, types incompatibles) est
  FAUSSE plutôt qu'une exception ; ``=`` / ``!=`` restent définis ;
- un calcul impossible (``NULL``, types incompatibles, division par zéro)
  donne ``NULL``, qui rend fausse la comparaison qui le suit ;
- ``AND`` / ``OR`` / ``NOT`` lisent ``NULL`` comme faux ;
- les dates des documents (chaînes ISO 8601) se comparent à ``NOW()`` et
  servent aux fonctions d'écart : la conversion est faite quand un côté est
  une date.

Le compilateur transforme l'arbre ANTLR en closures ``(run_ctx, params)``,
une fois par site d'appel : ``@state`` et le contrôle des chemins
``@IncomingEvent`` dépendent du bloc où la règle est appelée.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..clock import WorkflowClock
from ..exceptions import (
    InvalidArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
)
from ..values import resolve_value
from .generated.WorkflowParser import WorkflowParser
from .parser import _unquote

#: Valeur compilée : ``(run_ctx, params) -> valeur``.
Compiled = Callable[[Any, dict[str, Any]], Any]


# ----------------------------------------------------------------------
# Sémantique à l'exécution
# ----------------------------------------------------------------------


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Python 3.10 ne lit pas le suffixe « Z ».
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _align_dates(left: Any, right: Any) -> tuple[Any, Any]:
    """Convertit en dates quand UN côté en est une (``NOW()`` contre une
    date ISO d'un document) ; deux chaînes restent des chaînes."""
    if isinstance(left, datetime) or isinstance(right, datetime):
        a, b = _as_datetime(left), _as_datetime(right)
        if a is not None and b is not None:
            return a, b
    return left, right


def truthy(value: Any) -> bool:
    return bool(value) if value is not None else False


def equals(left: Any, right: Any) -> bool:
    left, right = _align_dates(left, right)
    try:
        return bool(left == right)
    except TypeError:  # datetimes naïve/aware
        return False


def compare(op: str, left: Any, right: Any) -> bool:
    if op == "=":
        return equals(left, right)
    if op in ("!=", "<>"):
        return not equals(left, right)
    if left is None or right is None:
        return False
    left, right = _align_dates(left, right)
    try:
        if op == "<":
            return bool(left < right)
        if op == "<=":
            return bool(left <= right)
        if op == ">":
            return bool(left > right)
        if op == ">=":
            return bool(left >= right)
    except TypeError:
        return False
    raise AssertionError(op)  # pragma: no cover


def arithmetic(op: str, left: Any, right: Any) -> Any:
    if left is None or right is None:
        return None
    try:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
    except (TypeError, ZeroDivisionError):
        return None
    raise AssertionError(op)  # pragma: no cover


def _between(divisor: float) -> Callable[[Any, Any], float | None]:
    def between(start: Any, end: Any) -> float | None:
        a, b = _as_datetime(start), _as_datetime(end)
        if a is None or b is None:
            return None
        try:
            return (b - a).total_seconds() / divisor
        except TypeError:  # naïve/aware
            return None

    return between


def _length(value: Any) -> int | None:
    return len(value) if isinstance(value, (str, list, dict)) else None


def _contains(container: Any, item: Any) -> bool:
    if isinstance(container, str):
        return isinstance(item, str) and item in container
    if isinstance(container, list):
        return any(equals(element, item) for element in container)
    if isinstance(container, dict):
        return item in container
    return False


#: Fonctions disponibles : nom (insensible à la casse) → (arité, fonction).
FUNCTIONS: dict[str, tuple[int, Callable[..., Any]]] = {
    "NOW": (0, lambda: WorkflowClock.now()),
    "LENGTH": (1, _length),
    "CONTAINS": (2, _contains),
    "DAYS_BETWEEN": (2, _between(86400.0)),
    "HOURS_BETWEEN": (2, _between(3600.0)),
    "MINUTES_BETWEEN": (2, _between(60.0)),
}


# ----------------------------------------------------------------------
# Compilation
# ----------------------------------------------------------------------


class ExpressionCompiler:
    """Compile un ``expression`` ANTLR en closure.

    Le visiteur fournit ce qui dépend du contexte de chargement : la
    fabrique de chemins ``@…`` (contrôle contre les schémas, liaison de
    ``@state``), les constantes et la levée d'erreurs positionnées.
    """

    def __init__(
        self,
        *,
        parameters: dict[str, type],
        constants: dict[str, Any],
        make_path: Callable[[str, Any], Any],
        error: Callable[[type, Any, str], Any],
    ) -> None:
        self._parameters = parameters
        self._constants = constants
        self._make_path = make_path
        self._error = error

    def compile(self, ctx) -> Compiled:
        P = WorkflowParser
        if isinstance(ctx, P.PrimaryContext):
            return self._primary(ctx.primaryExpression())

        if isinstance(ctx, P.NegateExpressionContext):
            inner = self.compile(ctx.expression())
            return lambda run_ctx, params: arithmetic("-", 0, inner(run_ctx, params))

        if isinstance(ctx, (P.MultiplyExpressionContext, P.AddExpressionContext)):
            left, right = (self.compile(e) for e in ctx.expression())
            op = ctx.op.text
            return lambda run_ctx, params: arithmetic(
                op, left(run_ctx, params), right(run_ctx, params)
            )

        if isinstance(ctx, P.CompareExpressionContext):
            left, right = (self.compile(e) for e in ctx.expression())
            op = ctx.op.text
            return lambda run_ctx, params: compare(
                op, left(run_ctx, params), right(run_ctx, params)
            )

        if isinstance(ctx, P.InExpressionContext):
            subject, *choices = (self.compile(e) for e in ctx.expression())
            negated = ctx.NOT() is not None

            def membership(run_ctx, params) -> bool:
                value = subject(run_ctx, params)
                found = any(equals(value, c(run_ctx, params)) for c in choices)
                return found != negated

            return membership

        if isinstance(ctx, P.NullExpressionContext):
            inner = self.compile(ctx.expression())
            negated = ctx.NOT() is not None
            return lambda run_ctx, params: (inner(run_ctx, params) is None) != negated

        if isinstance(ctx, P.NotExpressionContext):
            inner = self.compile(ctx.expression())
            return lambda run_ctx, params: not truthy(inner(run_ctx, params))

        if isinstance(ctx, P.AndExpressionContext):
            left, right = (self.compile(e) for e in ctx.expression())
            return lambda run_ctx, params: (
                truthy(left(run_ctx, params)) and truthy(right(run_ctx, params))
            )

        if isinstance(ctx, P.OrExpressionContext):
            left, right = (self.compile(e) for e in ctx.expression())
            return lambda run_ctx, params: (
                truthy(left(run_ctx, params)) or truthy(right(run_ctx, params))
            )

        raise AssertionError(type(ctx).__name__)  # pragma: no cover

    def _primary(self, ctx) -> Compiled:
        P = WorkflowParser
        if isinstance(ctx, P.NumericLiteralContext):
            value: Any = float(ctx.getText())
            return lambda run_ctx, params: value
        if isinstance(ctx, P.IntegerLiteralContext):
            value = int(ctx.getText())
            return lambda run_ctx, params: value
        if isinstance(ctx, P.StringLiteralContext):
            value = _unquote(ctx.getText())
            return lambda run_ctx, params: value
        if isinstance(ctx, P.BooleanLiteralContext):
            value = ctx.TRUE() is not None
            return lambda run_ctx, params: value
        if isinstance(ctx, P.NullLiteralContext):
            return lambda run_ctx, params: None
        if isinstance(ctx, P.ParenthesizedContext):
            return self.compile(ctx.expression())
        if isinstance(ctx, P.PathValueContext):
            path = self._make_path(ctx.contextPath().getText(), ctx)
            return lambda run_ctx, params: resolve_value(path, run_ctx)
        if isinstance(ctx, P.IdentifierContext):
            return self._identifier(ctx)
        if isinstance(ctx, P.FunctionCallContext):
            return self._function(ctx)
        raise AssertionError(type(ctx).__name__)  # pragma: no cover

    def _identifier(self, ctx) -> Compiled:
        # Paramètre de la règle d'abord (il masque une constante homonyme),
        # puis constante ; un nom inconnu est une erreur — contrairement aux
        # arguments d'appel, pas de repli « littéral » : une faute de frappe
        # deviendrait silencieusement une chaîne.
        name = ctx.getText()
        if name in self._parameters:
            return lambda run_ctx, params: params.get(name)
        if name in self._constants:
            value = self._constants[name]
            return lambda run_ctx, params: value
        self._error(
            InvalidArgumentNameError,
            ctx,
            f"unknown identifier {name!r} in rule body; parameters: "
            f"{sorted(self._parameters)}, constants: {sorted(self._constants)} "
            "(text literals take quotes)",
        )
        raise AssertionError  # pragma: no cover

    def _function(self, ctx) -> Compiled:
        name = ctx.key().getText()
        entry = FUNCTIONS.get(name.upper())
        if entry is None:
            self._error(
                InvalidMethodReferenceError,
                ctx,
                f"unknown function {name!r} in rule body; available: "
                f"{sorted(FUNCTIONS)}",
            )
        arity, func = entry
        arguments = [self.compile(e) for e in ctx.expression()]
        if len(arguments) != arity:
            self._error(
                InvalidArgumentValueError,
                ctx,
                f"function {name.upper()} expects {arity} argument(s), "
                f"got {len(arguments)}",
            )
        return lambda run_ctx, params: func(*(a(run_ctx, params) for a in arguments))
