"""API du playground : analyse (diagnostics + symboles) et simulation.

Deux endpoints :

- ``POST /api/analyze`` — analyse un script avec les règles paramétrées ;
  retourne les erreurs **positionnées** (syntaxe et sémantique), les
  symboles pour l'intellisense (événements, règles, actions, constantes,
  états) et un résumé structurel de la configuration ;
- ``POST /api/simulate`` — rejoue une suite d'événements sur le script
  (moteur complet en mémoire) et retourne états, actions poussées et
  journal fonctionnel.

Les règles métier n'existant pas côté navigateur, le panneau de
paramétrage les déclare (nom, paramètres typés, résultat simulé) ; le
serveur fabrique des callables à la signature exacte pour que la
validation des appels ``WHEN`` soit la vraie.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from urban_workflow import (
    FunctionRegistry,
    MemoryStorage,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
)
from urban_workflow.dsl import WorkflowConfigVisitor, WorkflowScriptParser
from urban_workflow.exceptions import DslSyntaxError, WorkflowError
from urban_workflow.outputs import default_memory_output
from urban_workflow.templating.context import json_safe

STATIC_DIR = Path(__file__).parent / "static"

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]*$")
_POSITIONED = re.compile(r"^(?:[^:\n]*:)?(\d+):(\d+):\s*(.*)$", re.DOTALL)

app = FastAPI(title="urban-workflow playground")


# ----------------------------------------------------------------------
# Modèles d'échange
# ----------------------------------------------------------------------


class RuleParam(BaseModel):
    name: str
    type: str = "TEXT"  # TEXT | INTEGER | DECIMAL


class RuleSetting(BaseModel):
    """Une règle métier paramétrée dans le panneau."""

    name: str
    params: list[RuleParam] = Field(default_factory=list)
    result: bool = True  # résultat simulé


class AnalyzeRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)


class SimulateRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Règles simulées
# ----------------------------------------------------------------------


def _build_registry(settings: list[RuleSetting]) -> FunctionRegistry:
    """Fabrique des callables à la signature exacte des règles paramétrées."""
    registry = FunctionRegistry("rule")
    for setting in settings:
        if not _IDENTIFIER.match(setting.name):
            continue
        params = [p.name for p in setting.params if _IDENTIFIER.match(p.name)]
        signature = ", ".join(["ctx", *params])
        namespace: dict[str, Any] = {}
        exec(
            f"def _rule({signature}):\n    return {bool(setting.result)}",
            namespace,
        )
        if setting.name not in registry:
            registry.add(setting.name, namespace["_rule"])
    return registry


# ----------------------------------------------------------------------
# Extraction de symboles (repli regex quand le script ne compile pas)
# ----------------------------------------------------------------------

_RE_EVENT = re.compile(r"\bDEFINE\s+EVENT\s+(\w+)", re.IGNORECASE)
_RE_RULE = re.compile(r"\bDEFINE\s+RULE\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE)
_RE_ACTION = re.compile(r"\bDEFINE\s+ACTION\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE)
_RE_CONST = re.compile(r"\bDEFINE\s+CONST\s+(\w+)", re.IGNORECASE)
_RE_STATE = re.compile(r"\bDEFINE\s+STATE\s+(\w+)", re.IGNORECASE)
_RE_PARAM = re.compile(r"(TEXT|INTEGER|DECIMAL)\s+(\w+)", re.IGNORECASE)


def _params_from_text(text: str) -> list[dict[str, str]]:
    return [
        {"name": name, "type": kind.upper()}
        for kind, name in _RE_PARAM.findall(text or "")
    ]


def _symbols_from_text(script: str) -> dict[str, Any]:
    return {
        "events": sorted(set(_RE_EVENT.findall(script))),
        "rules": [
            {"name": name, "params": _params_from_text(params)}
            for name, params in _RE_RULE.findall(script)
        ],
        "actions": [
            {"name": name, "params": _params_from_text(params)}
            for name, params in _RE_ACTION.findall(script)
        ],
        "constants": sorted(set(_RE_CONST.findall(script))),
        "states": sorted(set(_RE_STATE.findall(script))),
    }


_DSL_TYPE_NAMES = {str: "TEXT", int: "INTEGER", float: "DECIMAL"}


def _symbols_from_visitor(visitor: WorkflowConfigVisitor, config) -> dict[str, Any]:
    def declared(kind: str) -> list[dict[str, Any]]:
        return [
            {
                "name": d.name,
                "params": [
                    {"name": n, "type": _DSL_TYPE_NAMES.get(t, t.__name__.upper())}
                    for n, t in d.parameters.items()
                ],
                "comment": d.comment,
            }
            for d in visitor.declarations.values()
            if d.kind == kind
        ]

    return {
        "events": sorted(config.declared_events),
        "rules": declared("rule"),
        "actions": declared("action"),
        "constants": [
            {"name": c.key, "value": c.value, "comment": c.comment}
            for c in visitor.constants.values()
        ],
        "states": sorted(config.states),
    }


# ----------------------------------------------------------------------
# Erreurs positionnées
# ----------------------------------------------------------------------


def _error_entry(message: str, line: int = 1, column: int = 0) -> dict[str, Any]:
    return {"line": line, "column": column, "message": message, "severity": "error"}


def _positioned(exc: WorkflowError) -> dict[str, Any]:
    """Retrouve ``ligne:colonne`` dans le message des erreurs du visiteur."""
    match = _POSITIONED.match(str(exc))
    if match:
        return _error_entry(match.group(3), int(match.group(1)), int(match.group(2)))
    return _error_entry(str(exc))


def _summary(config) -> dict[str, Any]:
    return {
        "name": config.name,
        "version": config.version,
        "concurrency": config.concurrency,
        "label": config.label,
        "filters": dict(config.filters),
        "initializers": [
            {
                "event": init.event_name,
                "recursive": init.recursive,
                "switchs": [
                    {"target": s.target_state_name, "when": s.when_rule_text}
                    for s in init.switchs
                ],
            }
            for init in config.initializers.values()
        ],
        "states": [
            {
                "name": state.name,
                "label": state.label,
                "events": [
                    {
                        "name": event.name,
                        "transitions": [
                            {"target": t.target_state_name, "when": t.when_rule_text}
                            for t in event.transitions
                        ],
                    }
                    for event in state.events.values()
                ],
            }
            for state in config.states.values()
        ],
    }


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    summary: dict[str, Any] | None = None
    symbols = _symbols_from_text(request.script)

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    for error in parser.errors:
        errors.append(_error_entry(error.message, error.line, error.column))

    if not errors:
        visitor = WorkflowConfigVisitor(
            rules=_build_registry(request.rules), filename="playground"
        )
        try:
            config = parser.visit(visitor)
            if not parser.is_fragment:
                summary = _summary(config)
            symbols = _symbols_from_visitor(visitor, config)
        except DslSyntaxError as exc:
            errors.extend(
                _error_entry(e.message, e.line, e.column) for e in exc.errors
            )
        except WorkflowError as exc:
            errors.append(_positioned(exc))

    return {
        "ok": not errors,
        "is_fragment": parser.is_fragment,
        "errors": errors,
        "symbols": symbols,
        "summary": summary,
    }


@app.post("/api/simulate")
def simulate(request: SimulateRequest) -> dict[str, Any]:
    registry = _build_registry(request.rules)

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    try:
        parser.check()
        config = parser.visit(WorkflowConfigVisitor(rules=registry, filename="playground"))
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc), "steps": []}

    storage = MemoryStorage()
    processor = WorkflowProcessor(
        WorkflowsConfig().add_document(config), WorkflowFactory()
    )
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    engine = WorkflowEngine(processor)

    steps: list[dict[str, Any]] = []
    for payload in request.events:
        step: dict[str, Any] = {"event": payload.get("Name", "?")}
        try:
            contexts = engine.evaluate_event(payload)
        except Exception as exc:  # erreur de payload ou de règle : on la montre
            step["error"] = f"{type(exc).__name__}: {exc}"
            steps.append(step)
            continue

        step["impacted"] = [
            {
                "workflow": ctx.workflow.workflow_name,
                "external_id": ctx.workflow.external_id,
                "from_state": ctx.event.from_state,
                "to_state": ctx.event.to_state,
                "actions": [
                    {
                        "name": pushed.name,
                        "kind": pushed.kind,
                        "message": json_safe(pushed.execute_message),
                    }
                    for pushed in ctx.event.actions
                ],
                "log": list(ctx.functional_log),
            }
            for ctx in contexts
        ]
        steps.append(step)

    return {
        "ok": True,
        "steps": steps,
        "workflows": [
            {
                "workflow": w.workflow_name,
                "external_id": w.external_id,
                "state": w.current_state,
                "extended_datas": json_safe(w.extended_datas),
                "events": [
                    {"name": e.name, "from": e.from_state, "to": e.to_state}
                    for e in w.events
                ],
            }
            for w in storage.get_all(Workflow)
        ],
    }


# ----------------------------------------------------------------------
# Fichiers statiques
# ----------------------------------------------------------------------


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
