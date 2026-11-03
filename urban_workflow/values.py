"""Valeurs paresseuses résolues contre le contexte d'exécution.

Dans le projet source, les arguments d'action (``key = @Event.ExternalId``)
étaient des ``Func<RunContext, object>`` fabriqués par compilation
d'expressions. Ici, une valeur de configuration est au choix :

- un **littéral** JSON-compatible (str, int, float, bool, None, dict, list) ;
- une :class:`ContextRef`, référence ``@a.b.c`` résolue au moment de
  l'exécution contre le ``RunContext`` ;
- un **callable** ``(ctx) -> object`` pour les cas construits en Python.

:func:`resolve_value` normalise les trois formes.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .exceptions import ResolutionArgumentError

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _snake_case(name: str) -> str:
    return _CAMEL_RE.sub("_", name).lower()


def _resolve_segment(obj: Any, segment: str, full_path: str) -> Any:
    """Résout un segment de chemin sur ``obj``.

    Ordre de résolution (compatible avec les chemins CamelCase du DSL,
    ``@Event.ExternalId``, face aux attributs snake_case du portage) :

    1. clé exacte si ``obj`` est un mapping ;
    2. attribut au nom exact ;
    3. attribut au nom converti en snake_case ;
    4. clé des données étendues (``extended_datas``) de ``obj``.
    """

    if isinstance(obj, Mapping):
        if segment in obj:
            return obj[segment]
        raise ResolutionArgumentError(f"missing key {segment} in path {full_path}")

    if hasattr(obj, segment):
        return getattr(obj, segment)

    snake = _snake_case(segment)
    if hasattr(obj, snake):
        return getattr(obj, snake)

    extended = getattr(obj, "extended_datas", None)
    if isinstance(extended, Mapping) and segment in extended:
        return extended[segment]

    raise ResolutionArgumentError(f"missing key {segment} in path {full_path}")


@dataclass(frozen=True)
class ContextRef:
    """Référence ``@a.b.c`` vers une donnée du contexte d'exécution.

    ``path`` est stocké sans le ``@`` initial. L'instance est appelable :
    ``ref(ctx)`` retourne la valeur pointée ou lève
    :class:`~urban_workflow.exceptions.ResolutionArgumentError`.
    """

    path: str

    @classmethod
    def parse(cls, text: str) -> ContextRef:
        return cls(text[1:] if text.startswith("@") else text)

    def __call__(self, ctx: Any) -> Any:
        current = ctx
        for segment in self.path.split("."):
            current = _resolve_segment(current, segment, self.path)
        return current


#: Une valeur de configuration : littéral, référence contextuelle ou callable.
ContextValue = Any | ContextRef | Callable[[Any], Any]


def make_value(raw: Any) -> ContextValue:
    """Interprète une valeur brute de configuration.

    Les chaînes préfixées par ``@`` deviennent des :class:`ContextRef`
    (même convention que ``AddArgument`` dans le source) ; tout le reste
    est conservé tel quel.
    """
    if isinstance(raw, str) and raw.startswith("@"):
        return ContextRef.parse(raw)
    return raw


def resolve_value(value: ContextValue, ctx: Any) -> Any:
    """Résout une valeur de configuration contre le contexte."""
    if isinstance(value, ContextRef):
        return value(ctx)
    if callable(value):
        return value(ctx)
    return value
