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


_PATH_TOKEN_RE = re.compile(
    r"\.(?P<key>[A-Za-z_][A-Za-z0-9_$#]*)"
    r"|\[(?P<index>\d+)\]"
    r"|\['(?P<quoted>(?:[^']|'')*)'\]"
)


@dataclass(frozen=True)
class EventPath:
    """Chemin JSONPath ``$.a.b[0]`` vers le document de l'événement entrant.

    Extension DSL urban-workflow (``WHEN Regle(p = $.Montant)``). Le
    document est celui que valident les schémas : socle CamelCase
    (``Name``, ``IntegrationDate``…) + données métier — l'auteur d'un
    script raisonne donc sur le même objet que dans le YAML du schéma.

    Sous-ensemble volontaire : propriétés et index de liste, pas de filtres
    ni de jokers (une règle reçoit UNE valeur). Un chemin absent donne
    ``None`` (sémantique JSONPath « pas de correspondance », même
    convention que les chemins urban-json) plutôt qu'une erreur : un champ
    facultatif absent est un cas métier normal, que la règle tranche.
    """

    #: Segments : ``str`` pour une propriété, ``int`` pour un index.
    segments: tuple[str | int, ...] = ()

    @classmethod
    def parse(cls, text: str) -> EventPath:
        text = text.replace(" ", "")
        if not text.startswith("$"):
            raise ValueError(f"an event path starts with '$': {text!r}")
        segments: list[str | int] = []
        position = 1
        while position < len(text):
            match = _PATH_TOKEN_RE.match(text, position)
            if match is None:
                raise ValueError(f"invalid event path {text!r} at {position}")
            if match.group("key") is not None:
                segments.append(match.group("key"))
            elif match.group("index") is not None:
                segments.append(int(match.group("index")))
            else:
                segments.append(match.group("quoted").replace("''", "'"))
            position = match.end()
        return cls(tuple(segments))

    def __str__(self) -> str:
        parts = ["$"]
        for segment in self.segments:
            if isinstance(segment, int):
                parts.append(f"[{segment}]")
            elif re.fullmatch(r"[A-Za-z][A-Za-z0-9_$#]*", segment):
                parts.append(f".{segment}")
            else:
                parts.append("['" + segment.replace("'", "''") + "']")
        return "".join(parts)

    def resolve(self, document: Any) -> Any:
        current = document
        for segment in self.segments:
            if isinstance(segment, int):
                if not isinstance(current, list) or segment >= len(current):
                    return None
                current = current[segment]
            else:
                if not isinstance(current, Mapping) or segment not in current:
                    return None
                current = current[segment]
        return current

    def __call__(self, ctx: Any) -> Any:
        # Import local : values est un module de base, le serializer (moteur)
        # en dépend déjà — l'inverse au niveau module ferait un cycle.
        from .engine.serializer import event_to_document

        incoming = getattr(ctx, "incoming_event", None)
        if incoming is None:
            return None
        return self.resolve(event_to_document(incoming))


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
