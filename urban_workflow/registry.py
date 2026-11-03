"""Registre des règles et actions métier.

Remplace la machinerie ``MethodReference`` + compilation d'expressions du
source : une règle est un simple callable ``(ctx, **kwargs) -> bool``, une
action un callable ``(ctx, **kwargs) -> Any``, enregistrés par nom.

La validation des arguments nommés (celle que le visiteur DSL effectue à la
construction de la configuration) s'appuie sur ``inspect.signature``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from typing import Any

from .exceptions import (
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
)

ContextFunction = Callable[..., Any]


class FunctionRegistry:
    """Registre nommé de callables ``(ctx, **kwargs)``.

    ``kind`` n'est utilisé que pour les messages d'erreur ("rule"/"action").
    """

    def __init__(self, kind: str = "function") -> None:
        self._kind = kind
        self._functions: dict[str, ContextFunction] = {}

    # ------------------------------------------------------------------
    # Enregistrement
    # ------------------------------------------------------------------

    def add(self, name: str, func: ContextFunction) -> FunctionRegistry:
        if name in self._functions:
            raise DuplicatedArgumentNameError(f"{self._kind} name {name!r} is already registered")
        self._functions[name] = func
        return self

    def register(self, name: str | None = None) -> Callable[[ContextFunction], ContextFunction]:
        """Décorateur : ``@rules.register("IsMajor")`` ou ``@rules.register()``."""

        def decorator(func: ContextFunction) -> ContextFunction:
            self.add(name or func.__name__, func)
            return func

        return decorator

    # ------------------------------------------------------------------
    # Résolution
    # ------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        return name in self._functions

    def get(self, name: str) -> ContextFunction:
        try:
            return self._functions[name]
        except KeyError:
            raise InvalidMethodReferenceError(
                f"no {self._kind} registered under name {name!r}"
            ) from None

    def names(self) -> Iterable[str]:
        return self._functions.keys()

    # ------------------------------------------------------------------
    # Validation des arguments nommés (utilisée par le visiteur DSL)
    # ------------------------------------------------------------------

    def validate_call(self, name: str, argument_names: Iterable[str]) -> None:
        """Vérifie que ``name(arg=…)`` est un appel valide.

        Lève :class:`InvalidMethodReferenceError` si la fonction est
        inconnue, :class:`DuplicatedArgumentNameError` si un argument est
        passé deux fois, :class:`InvalidArgumentNameError` si un argument
        ne figure pas dans la signature (sauf ``**kwargs``), et
        :class:`MissingArgumentNameError` si un paramètre sans valeur par
        défaut n'est pas fourni.
        """

        func = self.get(name)
        provided = list(argument_names)

        duplicates = {a for a in provided if provided.count(a) > 1}
        if duplicates:
            raise DuplicatedArgumentNameError(
                f"duplicated argument(s) {sorted(duplicates)} in call to {self._kind} {name!r}"
            )

        parameters = list(inspect.signature(func).parameters.values())

        # Le premier paramètre positionnel est le contexte : il n'est pas nommable.
        if parameters and parameters[0].kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            parameters = parameters[1:]

        accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters)
        named = {
            p.name: p
            for p in parameters
            if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }

        if not accepts_kwargs:
            unknown = [a for a in provided if a not in named]
            if unknown:
                raise InvalidArgumentNameError(
                    f"unknown argument(s) {unknown} in call to {self._kind} {name!r}; "
                    f"expected: {sorted(named)}"
                )

        missing = [
            p.name
            for p in named.values()
            if p.default is inspect.Parameter.empty and p.name not in provided
        ]
        if missing:
            raise MissingArgumentNameError(
                f"missing argument(s) {missing} in call to {self._kind} {name!r}"
            )
