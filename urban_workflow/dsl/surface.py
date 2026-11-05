"""Modèle « de surface » d'un script DSL : structure fidèle + rendu canonique.

Contrairement au :class:`~urban_workflow.dsl.visitor.WorkflowConfigVisitor`,
qui compile le script en configuration exécutable (closures, validation des
signatures), ce module extrait une représentation **structurelle et
sérialisable** du script : états, transitions, déclarations — les expressions
(gardes ``WHEN``, blocs ``EXECUTE``/``STORE``, délais) restent du **texte
source brut**. C'est le format d'échange de l'outillage (vue diagramme du
playground, génération de scripts) :

- :func:`extract_surface` — script DSL → :class:`SurfaceModel` (sans exiger
  l'enregistrement des règles métier : aucune validation sémantique) ;
- :func:`render_script` — :class:`SurfaceModel` → script DSL canonique.

Propriété de point fixe testée : ``render(extract(render(m))) ==
render(m)``. Limite assumée (ambiguïté de la grammaire source) : dans une
branche sans garde propre dont le premier bloc d'exécution commence par
``WHEN``, la re-analyse rattache ce ``WHEN`` à la branche ; l'aller-retour
par :func:`render_script` reproduit dans ce cas la lecture du parseur.

Les scripts ``FRAGMENT`` et les scripts à ``INCLUDE`` ne sont pas
représentables (un modèle = un workflow autonome) : :class:`SurfaceError`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..exceptions import WorkflowError
from .parser import WorkflowScriptParser, _unquote

__all__ = [
    "SurfaceConst",
    "SurfaceError",
    "SurfaceEvent",
    "SurfaceFunction",
    "SurfaceHandler",
    "SurfaceInitializer",
    "SurfaceModel",
    "SurfaceState",
    "SurfaceStateAction",
    "SurfaceTransition",
    "extract_surface",
    "render_script",
]


class SurfaceError(WorkflowError):
    """Script non représentable en modèle de surface (fragment, INCLUDE…)."""


# ----------------------------------------------------------------------
# Modèle
# ----------------------------------------------------------------------


@dataclass
class SurfaceEvent:
    """``DEFINE EVENT nom 'libellé' [AS @schema] [UNIQUE (Prop, …)];``"""

    name: str
    label: str = ""
    schema_ref: str = ""
    unique: list[str] = field(default_factory=list)


@dataclass
class SurfaceFunction:
    """``DEFINE RULE|ACTION nom (TYPE param, …) 'libellé' [AS corps];``"""

    name: str
    params: list[dict[str, str]] = field(default_factory=list)  # {type, name}
    label: str = ""
    #: Corps d'une règle écrite dans le DSL (texte source brut), "" sinon.
    body: str = ""


@dataclass
class SurfaceConst:
    """``DEFINE CONST nom valeur 'libellé';`` — ``value`` = texte source brut."""

    name: str
    value: str = ""
    label: str = ""


@dataclass
class SurfaceInitializer:
    """Une entrée de ``INITIALIZE WORKFLOW``."""

    event: str
    switch: str
    when: str = ""  # texte source de la garde, "" = sans garde
    recursive: bool = False


@dataclass
class SurfaceTransition:
    """Une branche de ``ON EVENT`` / ``EXPIRE AFTER`` (``switch_state``).

    ``executes`` : blocs d'exécution complets (texte source brut, chacun
    pouvant porter ``WHEN``/``WAITING``/``EXECUTE``/``STORE``).
    ``switch`` vide = branche à actions seules, sans bascule.
    """

    when: str = ""
    executes: list[str] = field(default_factory=list)
    switch: str = ""


@dataclass
class SurfaceHandler:
    """``ON EVENT nom`` (``event``) ou ``EXPIRE AFTER délai`` (``expire_after``)."""

    event: str = ""
    expire_after: str = ""  # texte source du délai, ex. "3 DAY"
    transitions: list[SurfaceTransition] = field(default_factory=list)


@dataclass
class SurfaceStateAction:
    """``ON ENTER|EXIT|ENTER AND EXIT STATE`` + bloc d'exécution brut."""

    trigger: str  # "ENTER" | "EXIT" | "ENTER AND EXIT"
    execute: str = ""


@dataclass
class SurfaceState:
    """``DEFINE STATE nom 'libellé' [AS @schema] …;``"""

    name: str
    label: str = ""
    schema_ref: str = ""
    actions: list[SurfaceStateAction] = field(default_factory=list)
    handlers: list[SurfaceHandler] = field(default_factory=list)


@dataclass
class SurfaceModel:
    """Un script DSL complet, sous forme structurelle sérialisable."""

    name: str = ""
    version: int = 1
    concurrency: int = 1
    description: str = ""
    filters: list[dict[str, str]] = field(default_factory=list)  # {key, value}
    events: list[SurfaceEvent] = field(default_factory=list)
    rules: list[SurfaceFunction] = field(default_factory=list)
    actions: list[SurfaceFunction] = field(default_factory=list)
    consts: list[SurfaceConst] = field(default_factory=list)
    initializers: list[SurfaceInitializer] = field(default_factory=list)
    states: list[SurfaceState] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurfaceModel:
        def functions(items: Any) -> list[SurfaceFunction]:
            return [
                SurfaceFunction(
                    name=str(f.get("name", "")),
                    params=[
                        {
                            "type": str(p.get("type", "TEXT")),
                            "name": str(p.get("name", "")),
                        }
                        for p in f.get("params", [])
                    ],
                    label=str(f.get("label", "")),
                    body=str(f.get("body", "") or ""),
                )
                for f in items or []
            ]

        return cls(
            name=str(data.get("name", "")),
            version=int(data.get("version", 1) or 1),
            concurrency=int(data.get("concurrency", 1) or 1),
            description=str(data.get("description", "")),
            filters=[
                {"key": str(f.get("key", "")), "value": str(f.get("value", ""))}
                for f in data.get("filters", [])
            ],
            events=[
                SurfaceEvent(
                    name=str(e.get("name", "")),
                    label=str(e.get("label", "")),
                    schema_ref=str(e.get("schema_ref", "")),
                    unique=[str(u) for u in e.get("unique", [])],
                )
                for e in data.get("events", [])
            ],
            rules=functions(data.get("rules")),
            actions=functions(data.get("actions")),
            consts=[
                SurfaceConst(
                    name=str(c.get("name", "")),
                    value=str(c.get("value", "")),
                    label=str(c.get("label", "")),
                )
                for c in data.get("consts", [])
            ],
            initializers=[
                SurfaceInitializer(
                    event=str(i.get("event", "")),
                    switch=str(i.get("switch", "")),
                    when=str(i.get("when", "")),
                    recursive=bool(i.get("recursive", False)),
                )
                for i in data.get("initializers", [])
            ],
            states=[
                SurfaceState(
                    name=str(s.get("name", "")),
                    label=str(s.get("label", "")),
                    schema_ref=str(s.get("schema_ref", "")),
                    actions=[
                        SurfaceStateAction(
                            trigger=str(a.get("trigger", "ENTER")),
                            execute=str(a.get("execute", "")),
                        )
                        for a in s.get("actions", [])
                    ],
                    handlers=[
                        SurfaceHandler(
                            event=str(h.get("event", "")),
                            expire_after=str(h.get("expire_after", "")),
                            transitions=[
                                SurfaceTransition(
                                    when=str(t.get("when", "")),
                                    executes=[
                                        str(x) for x in t.get("executes", [])
                                    ],
                                    switch=str(t.get("switch", "")),
                                )
                                for t in h.get("transitions", [])
                            ],
                        )
                        for h in s.get("handlers", [])
                    ],
                )
                for s in data.get("states", [])
            ],
        )


# ----------------------------------------------------------------------
# Extraction (script → modèle)
# ----------------------------------------------------------------------


def _snippet(ctx) -> str:
    """Texte source d'un sous-arbre, lignes de continuation désindentées.

    La première ligne commence au premier token ; les suivantes portent leur
    indentation absolue d'origine, ramenée à une indentation **relative** à
    la colonne de départ (le rendu pourra les réindenter uniformément).
    """
    stream = ctx.start.getInputStream()
    text = stream.getText(ctx.start.start, ctx.stop.stop)
    lines = text.splitlines()
    if len(lines) <= 1:
        return text.strip()
    base = ctx.start.column
    result = [lines[0].rstrip()]
    for line in lines[1:]:
        line = line.rstrip()
        drop = 0
        while drop < len(line) and drop < base and line[drop] == " ":
            drop += 1
        result.append(line[drop:])
    return "\n".join(result)


def _optional_label(ctx) -> str:
    comment = ctx.comment()
    return _unquote(comment.getText()) if comment is not None else ""


def _function(ctx) -> SurfaceFunction:
    declared = SurfaceFunction(name=ctx.key().getText(), label=_optional_label(ctx))
    parameters = ctx.parameters()
    if parameters is not None:
        declared.params = [
            {"type": p.type_().getText(), "name": p.key().getText()}
            for p in parameters.parameter()
        ]
    body = getattr(ctx, "ruleBody", None)
    if body is not None:
        declared.body = _snippet(body)
    return declared


def extract_surface(source: str, filename: str = "") -> SurfaceModel:
    """Analyse ``source`` et retourne son :class:`SurfaceModel`.

    Lève :class:`~urban_workflow.exceptions.DslSyntaxError` sur erreur de
    syntaxe et :class:`SurfaceError` pour un fragment ou un script à
    ``INCLUDE``. Aucune règle métier n'est requise : l'extraction est
    purement structurelle.
    """
    parser = WorkflowScriptParser.parse_string(source, filename=filename).check()

    if parser.is_fragment:
        raise SurfaceError("un FRAGMENT n'est pas représentable en diagramme")
    if parser.includes:
        raise SurfaceError(
            "les scripts à INCLUDE ne sont pas représentables en diagramme "
            f"(inclusions : {', '.join(parser.includes)})"
        )

    full = parser.tree.script_full()
    model = SurfaceModel(name=full.key().getText())

    if full.VERSION() is not None:
        model.version = int(full.versionNumber.getText())
    if full.concurency() is not None:
        model.concurrency = int(full.concurency().number().getText())
    if full.DESCRIPTION() is not None:
        model.description = _unquote(full.comment().getText())
    if full.MATCHING() is not None:
        model.filters = [
            {
                "key": matching.key().getText(),
                "value": _unquote(matching.string().getText()),
            }
            for matching in full.matchings().matching()
        ]

    for statement in full.define_referenciel_statement():
        event = statement.event_declaration_statement()
        rule = statement.rule_declaration_statement()
        action = statement.action_declaration_statement()
        const = statement.constant_declaration()
        if event is not None:
            declared = SurfaceEvent(
                name=event.key().getText(), label=_optional_label(event)
            )
            if event.AS() is not None:
                declared.schema_ref = event.schemaRef.getText().lstrip("@")
            if event.unique_keys() is not None:
                declared.unique = [
                    key.getText() for key in event.unique_keys().key()
                ]
            model.events.append(declared)
        elif rule is not None:
            model.rules.append(_function(rule))
        elif action is not None:
            model.actions.append(_function(action))
        elif const is not None:
            model.consts.append(
                SurfaceConst(
                    name=const.key().getText(),
                    value=_snippet(const.value()),
                    label=_optional_label(const),
                )
            )

    initializing = full.initializing()
    if initializing is not None:
        for item in initializing.initializing_item():
            model.initializers.append(
                SurfaceInitializer(
                    event=item.key(0).getText(),
                    switch=item.key(1).getText(),
                    when=(
                        _snippet(item.rule_conditions())
                        if item.WHEN() is not None
                        else ""
                    ),
                    recursive=item.RECURSIVE() is not None,
                )
            )

    for statement in full.define_state_statement():
        state_ctx = statement.state_()
        state = SurfaceState(
            name=state_ctx.key().getText(), label=_optional_label(state_ctx)
        )
        if state_ctx.AS() is not None:
            state.schema_ref = state_ctx.schemaRef.getText().lstrip("@")

        for execute in state_ctx.execute():
            if execute.AND() is not None:
                trigger = "ENTER AND EXIT"
            elif execute.ENTER() is not None:
                trigger = "ENTER"
            else:
                trigger = "EXIT"
            state.actions.append(
                SurfaceStateAction(
                    trigger=trigger, execute=_snippet(execute.execute2())
                )
            )

        for on_event in state_ctx.on_event_statement():
            handler = SurfaceHandler()
            if on_event.EXPIRE() is not None:
                handler.expire_after = _snippet(on_event.delay())
            else:
                handler.event = on_event.key().getText()
            for switch_state in on_event.switch_state():
                handler.transitions.append(
                    SurfaceTransition(
                        when=(
                            _snippet(switch_state.rule_conditions())
                            if switch_state.WHEN() is not None
                            else ""
                        ),
                        executes=[
                            _snippet(execute2)
                            for execute2 in switch_state.execute2()
                        ],
                        switch=(
                            switch_state.key().getText()
                            if switch_state.SWITCH() is not None
                            else ""
                        ),
                    )
                )
            state.handlers.append(handler)

        model.states.append(state)

    return model


# ----------------------------------------------------------------------
# Rendu (modèle → script)
# ----------------------------------------------------------------------


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _emit(lines: list[str], snippet: str, indent: str) -> None:
    """Ajoute un snippet multi-ligne, réindenté sous ``indent``."""
    for line in snippet.splitlines():
        lines.append(indent + line if line else "")


def render_script(model: SurfaceModel) -> str:
    """Rend le script DSL canonique du modèle.

    Le résultat n'est pas validé ici : le re-passer à l'analyse (parseur +
    visiteur) est la validation d'aller-retour attendue de l'outillage.
    """
    lines: list[str] = [f"NAME {model.name} VERSION {model.version}"]

    if model.concurrency != 1:
        lines.append(f"CONCURENCY {model.concurrency}")
    if model.description:
        lines.append(f"DESCRIPTION {_quote(model.description)}")
    if model.filters:
        inner = " ".join(
            f"{item['key']} = {_quote(item['value'])}" for item in model.filters
        )
        lines.append(f"MATCHING ({inner})")
    lines.append("")

    for event in model.events:
        head = f"DEFINE EVENT  {event.name}"
        if event.label:
            head += f" {_quote(event.label)}"
        extras: list[str] = []
        if event.schema_ref:
            extras.append(f"AS @{event.schema_ref}")
        if event.unique:
            extras.append(f"UNIQUE ({', '.join(event.unique)})")
        if extras:
            lines.append(head)
            lines.append(f"    {' '.join(extras)};")
        else:
            lines.append(f"{head};")

    def declare(keyword: str, declared: SurfaceFunction) -> None:
        signature = ", ".join(
            f"{param['type']} {param['name']}" for param in declared.params
        )
        head = f"DEFINE {keyword} {declared.name} ({signature})"
        if declared.label:
            head += f" {_quote(declared.label)}"
        if declared.body:
            # Corps multi-lignes : continuations réindentées sous la règle.
            body = declared.body.replace("\n", "\n        ")
            head += f"\n    AS {body}"
        lines.append(f"{head};")

    for rule in model.rules:
        declare("RULE  ", rule)
    for action in model.actions:
        declare("ACTION", action)
    for const in model.consts:
        head = f"DEFINE CONST  {const.name} {const.value}"
        if const.label:
            head += f" {_quote(const.label)}"
        lines.append(f"{head};")

    if model.initializers:
        lines.append("")
        lines.append("INITIALIZE WORKFLOW")
        for init in model.initializers:
            suffix = (" RECURSIVE" if init.recursive else "") + f" SWITCH {init.switch}"
            if init.when and "\n" not in init.when:
                lines.append(f"    ON EVENT {init.event} WHEN {init.when}{suffix}")
            elif init.when:
                lines.append(f"    ON EVENT {init.event}")
                _emit(lines, f"WHEN {init.when}", "        ")
                lines.append(f"       {suffix}")
            else:
                lines.append(f"    ON EVENT {init.event}{suffix}")

    for state in model.states:
        lines.append("")
        head = f"DEFINE STATE {state.name}"
        if state.label:
            head += f" {_quote(state.label)}"
        if state.schema_ref:
            head += f" AS @{state.schema_ref}"
        lines.append(head)

        for state_action in state.actions:
            lines.append(f"    ON {state_action.trigger} STATE")
            _emit(lines, state_action.execute, "        ")

        for handler in state.handlers:
            if handler.expire_after:
                lines.append(f"    EXPIRE AFTER {handler.expire_after}")
            else:
                lines.append(f"    ON EVENT {handler.event}")
            for transition in handler.transitions:
                indent = "        "
                if transition.when:
                    _emit(lines, f"WHEN {transition.when}", indent)
                    indent = "            "
                for execute in transition.executes:
                    _emit(lines, execute, indent)
                if transition.switch:
                    lines.append(f"{indent}SWITCH {transition.switch}")
        lines.append(";")

    lines.append("")
    return "\n".join(lines)
