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
_PATH_ROOT_RE = re.compile(r"@(?P<root>[A-Za-z][A-Za-z0-9_$#]*)")


def parse_path_segments(text: str) -> tuple[str, tuple[str | int, ...]]:
    """``@Racine.a[0]['b']`` → ``("Racine", ("a", 0, "b"))``."""
    text = text.replace(" ", "")
    root = _PATH_ROOT_RE.match(text)
    if root is None:
        raise ValueError(f"a path starts with '@Root': {text!r}")
    segments: list[str | int] = []
    position = root.end()
    while position < len(text):
        match = _PATH_TOKEN_RE.match(text, position)
        if match is None:
            raise ValueError(f"invalid path {text!r} at {position}")
        if match.group("key") is not None:
            segments.append(match.group("key"))
        elif match.group("index") is not None:
            segments.append(int(match.group("index")))
        else:
            segments.append(match.group("quoted").replace("''", "'"))
        position = match.end()
    return root.group("root"), tuple(segments)


@dataclass(frozen=True)
class DocumentPath:
    """Chemin JSONPath ``@Racine.a.b[0]`` dans un document JSON du contexte.

    Sous-ensemble volontaire : propriétés et index de liste, pas de filtres
    ni de jokers (une règle reçoit UNE valeur). Un chemin absent donne
    ``None`` (sémantique JSONPath « pas de correspondance », même
    convention que les chemins urban-json) plutôt qu'une erreur : un champ
    facultatif absent est un cas métier normal, que la règle tranche.
    """

    ROOT = ""

    #: Segments : ``str`` pour une propriété, ``int`` pour un index.
    segments: tuple[str | int, ...] = ()

    def __str__(self) -> str:
        parts = ["@" + self.ROOT]
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

    def document(self, ctx: Any) -> Any:  # pragma: no cover - abstrait
        raise NotImplementedError

    def __call__(self, ctx: Any) -> Any:
        return self.resolve(self.document(ctx))


@dataclass(frozen=True)
class EventPath(DocumentPath):
    """``@IncomingEvent.…`` : le document de l'événement entrant.

    Le document est celui que valident les schémas (socle CamelCase +
    données métier) : l'auteur d'un script raisonne sur le même objet que
    dans le YAML du schéma et la vue Événements. Il ne porte rien de propre
    à un workflow (pas d'état de départ/d'arrivée) : un même événement peut
    être traité en parallèle par plusieurs workflows.
    """

    ROOT = "IncomingEvent"

    @classmethod
    def parse(cls, text: str) -> EventPath:
        _, segments = parse_path_segments(text)
        return cls(segments)

    def document(self, ctx: Any) -> Any:
        # Import local : values est un module de base, le serializer (moteur)
        # en dépend déjà — l'inverse au niveau module ferait un cycle.
        from .engine.serializer import event_to_document

        incoming = getattr(ctx, "incoming_event", None)
        if incoming is None:
            return None
        return event_to_document(incoming)


@dataclass(frozen=True)
class StatePath(DocumentPath):
    """``@state.…`` : l'instance de l'état du bloc ``DEFINE STATE`` courant.

    Liée au chargement au NOM de l'état du bloc où elle est écrite : dans
    ``DEFINE STATE X``, ``@state`` est toujours une instance de X — la plus
    récente, qu'on évalue une règle de ``ON EVENT`` (X est l'état courant)
    ou une action de ``ON ENTER`` (l'instance qui vient d'être créée).
    """

    ROOT = "state"

    state_name: str = ""

    @classmethod
    def parse(cls, text: str, state_name: str) -> StatePath:
        _, segments = parse_path_segments(text)
        return cls(segments, state_name)

    def document(self, ctx: Any) -> Any:
        instance = find_state_instance(ctx, self.state_name)
        if instance is None:
            # Workflow antérieur aux instances d'état : seul le nom est sûr.
            return {"Name": self.state_name}
        return state_document(instance)


def find_state_instance(ctx: Any, state_name: str) -> Any:
    """Instance la plus récente de ``state_name`` (en attente d'abord)."""
    pending = list(getattr(ctx, "pending_states", None) or [])
    workflow = getattr(ctx, "workflow", None)
    history = list(getattr(workflow, "states", None) or [])
    for instance in reversed(history + pending):
        if instance.name == state_name:
            return instance
    return None


def state_document(instance: Any) -> dict[str, Any]:
    """Document « format fil » d'une instance d'état (socle + métier)."""
    document: dict[str, Any] = dict(instance.extended_datas)
    document["Name"] = instance.name
    document["Uuid"] = str(instance.uuid)
    if instance.creation_date is not None:
        document["CreationDate"] = instance.creation_date.isoformat()
    if instance.event_id is not None:
        document["EventId"] = str(instance.event_id)
    return document


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
