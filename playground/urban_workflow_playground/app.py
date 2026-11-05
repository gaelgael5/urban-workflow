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

import hashlib
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
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
from urban_workflow.dsl import (
    SurfaceError,
    SurfaceModel,
    WorkflowConfigVisitor,
    WorkflowScriptParser,
    extract_surface,
    render_script,
)
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


class SchemaSetting(BaseModel):
    """Un schéma d'événement (JSON Schema en YAML) paramétré dans le panneau."""

    name: str
    yaml: str


class AnalyzeRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)


class SimulateRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


class DiagramRequest(BaseModel):
    script: str


class GenerateRequest(BaseModel):
    """Modèle de surface (vue diagramme) → script DSL + validation."""

    model: dict[str, Any]
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)


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


def _build_schema_registry(
    settings: list[SchemaSetting],
) -> tuple[Any, list[str]]:
    """Charge les schémas du panneau ; retourne (registre | None, erreurs)."""
    if not settings:
        return None, []
    try:
        from urban_workflow.schemas import SchemaRegistry
        registry = SchemaRegistry()
    except ImportError:
        return None, [
            "Schémas indisponibles : installer l'extra "
            "urban-workflow[schemas] (PyYAML + jsonschema)."
        ]

    from urban_workflow.schemas import BASE_EVENT_SCHEMA

    reserved = set(BASE_EVENT_SCHEMA["properties"])
    problems: list[str] = []
    for setting in settings:
        try:
            registry.add_yaml(setting.name, setting.yaml)
        except Exception as exc:
            problems.append(f"schéma {setting.name!r} : {exc}")
            continue
        # Les champs du socle sont validés par BASE_EVENT_SCHEMA sur TOUT
        # événement : un schéma métier qui les redéfinit ajouterait une
        # contrainte contradictoire (Uuid entier vs format uuid) que plus
        # aucun événement ne pourrait satisfaire. Refusé ici, côté serveur,
        # pour que l'éditeur visuel ne soit pas la seule barrière.
        clash = sorted(reserved & set(registry.get(setting.name).get("properties", {})))
        if clash:
            problems.append(
                f"schéma {setting.name!r} : {', '.join(clash)} "
                "appartien(nen)t au socle commun des événements et ne se "
                "redéfini(ssen)t pas dans un schéma métier"
            )
    return registry, problems


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


def _symbols_from_visitor(
    visitor: WorkflowConfigVisitor, config, script: str
) -> dict[str, Any]:
    # build() ajoute aux événements déclarés ceux qui ne sont qu'utilisés
    # (ON EVENT sans DEFINE EVENT) : on les distingue par le texte pour que
    # la vue « Événements » propose de les déclarer.
    declared_in_text = set(_RE_EVENT.findall(script))

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
        "event_details": [
            {
                "name": d.name,
                "label": d.label,
                "schema_ref": d.schema_ref,
                "unique": list(d.dedup_keys),
                "declared": d.name in declared_in_text,
            }
            # Tous les événements métier (et non plus seulement ceux qui
            # portent AS/UNIQUE) : la vue « Événements » les liste tous. Les
            # techniques ($_result, __expired) ne sont pas éditables.
            for d in config.declared_events.values()
            if not d.name.startswith(("$", "__"))
        ],
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


def _flatten_schema_paths(
    properties: dict[str, Any], prefix: str = "", depth: int = 0
) -> list[dict[str, str]]:
    """Chemins ``$.…`` proposés par l'intellisense, avec leur type.

    Objets descendus (``Client.Pays``), listes d'objets via leur premier
    élément (``Lignes[0].Qte``) — la même forme que la syntaxe acceptée par
    le DSL. Profondeur bornée : un schéma récursif ne fait pas boucler.
    """
    paths: list[dict[str, str]] = []
    if depth > 4:
        return paths
    for name, schema in properties.items():
        if not isinstance(schema, dict):
            continue
        path = f"{prefix}{name}"
        kind = schema.get("type", "")
        kind = kind if isinstance(kind, str) else "|".join(kind)
        paths.append({"path": path, "type": kind or "any"})
        if isinstance(schema.get("properties"), dict):
            paths.extend(_flatten_schema_paths(schema["properties"], f"{path}.", depth + 1))
        items = schema.get("items")
        if isinstance(items, dict):
            paths.append({"path": f"{path}[0]", "type": items.get("type", "any")})
            if isinstance(items.get("properties"), dict):
                paths.extend(
                    _flatten_schema_paths(items["properties"], f"{path}[0].", depth + 1)
                )
    return paths


def _event_properties(symbols: dict[str, Any], schema_registry) -> dict[str, list]:
    """Pour chaque événement : socle commun + propriétés de son schéma."""
    from urban_workflow.schemas import BASE_EVENT_SCHEMA

    refs = {d["name"]: d.get("schema_ref", "") for d in symbols.get("event_details", [])}
    names = list(refs) or [
        e for e in symbols.get("events", []) if not e.startswith(("$", "__"))
    ]
    result: dict[str, list] = {}
    for name in names:
        properties = dict(BASE_EVENT_SCHEMA["properties"])
        ref = refs.get(name, "")
        if ref and schema_registry is not None and ref in schema_registry:
            properties.update(schema_registry.get(ref).get("properties") or {})
        result[name] = _flatten_schema_paths(properties)
    return result


def _summary(config) -> dict[str, Any]:
    return {
        "name": config.name,
        "version": config.version,
        "concurrency": config.concurrency,
        "label": config.label,
        "filters": dict(config.filters),
        "events": [
            {
                "name": d.name,
                "label": d.label,
                "schema_ref": d.schema_ref,
                "unique": list(d.dedup_keys),
            }
            for d in config.declared_events.values()
            if not d.name.startswith(("$_", "__"))
        ],
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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # Sonde volontairement triviale : le playground n'a ni base ni dépendance
    # externe, « le process répond » est tout ce qu'il y a à vérifier. Visée
    # par le HEALTHCHECK de l'image et par l'étape de santé de dev-deploy.sh.
    return {"status": "ok"}


@app.get("/api/base-event-schema")
def base_event_schema() -> dict[str, Any]:
    # Source unique du socle : la vue « Événements » l'affiche en lecture
    # seule sans en garder une copie côté navigateur qui divergerait.
    from urban_workflow.schemas import BASE_EVENT_SCHEMA

    return BASE_EVENT_SCHEMA


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    summary: dict[str, Any] | None = None
    symbols = _symbols_from_text(request.script)

    schema_registry, schema_problems = _build_schema_registry(request.schemas)
    errors.extend(_error_entry(problem) for problem in schema_problems)

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    for error in parser.errors:
        errors.append(_error_entry(error.message, error.line, error.column))

    if not errors:
        visitor = WorkflowConfigVisitor(
            rules=_build_registry(request.rules),
            filename="playground",
            schemas=schema_registry,
        )
        try:
            config = parser.visit(visitor)
            if not parser.is_fragment:
                summary = _summary(config)
            symbols = _symbols_from_visitor(visitor, config, request.script)
        except DslSyntaxError as exc:
            errors.extend(
                _error_entry(e.message, e.line, e.column) for e in exc.errors
            )
        except WorkflowError as exc:
            errors.append(_positioned(exc))

    symbols["schemas"] = sorted(s.name for s in request.schemas)
    symbols.setdefault("event_details", [])

    # Propriétés connues pour la complétion de UNIQUE (…) : socle commun +
    # properties de tous les schémas du panneau.
    properties = {"ExternalId", "EventDate", "CreationDate", "DedupKey"}
    if schema_registry is not None:
        for setting in request.schemas:
            if setting.name in schema_registry:
                schema = schema_registry.get(setting.name)
                properties.update(schema.get("properties", {}))
    symbols["payload_properties"] = sorted(properties)
    symbols["event_properties"] = _event_properties(symbols, schema_registry)
    from urban_workflow.schemas import BASE_EVENT_SCHEMA

    symbols["base_paths"] = _flatten_schema_paths(BASE_EVENT_SCHEMA["properties"])

    return {
        "ok": not errors,
        "is_fragment": parser.is_fragment,
        "errors": errors,
        "symbols": symbols,
        "summary": summary,
    }


@app.post("/api/diagram")
def diagram(request: DiagramRequest) -> dict[str, Any]:
    """Script DSL → modèle de surface (structure fidèle pour la vue diagramme)."""
    try:
        model = extract_surface(request.script, filename="playground")
    except DslSyntaxError as exc:
        return {
            "ok": False,
            "errors": [_error_entry(e.message, e.line, e.column) for e in exc.errors],
            "model": None,
        }
    except SurfaceError as exc:
        return {"ok": False, "errors": [_error_entry(str(exc))], "model": None}
    return {"ok": True, "errors": [], "model": model.to_dict()}


@app.post("/api/generate")
def generate(request: GenerateRequest) -> dict[str, Any]:
    """Modèle de surface → script DSL canonique, validé par l'analyse réelle."""
    script = render_script(SurfaceModel.from_dict(request.model))
    analysis = analyze(
        AnalyzeRequest(
            script=script, rules=request.rules, schemas=request.schemas
        )
    )
    return {
        "ok": analysis["ok"],
        "script": script,
        "errors": analysis["errors"],
        "summary": analysis["summary"],
    }


@app.post("/api/simulate")
def simulate(request: SimulateRequest) -> dict[str, Any]:
    registry = _build_registry(request.rules)

    schema_registry, schema_problems = _build_schema_registry(request.schemas)
    if schema_problems:
        return {"ok": False, "error": " ; ".join(schema_problems), "steps": []}

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    try:
        parser.check()
        config = parser.visit(
            WorkflowConfigVisitor(
                rules=registry, filename="playground", schemas=schema_registry
            )
        )
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
                    {
                        "name": e.name, "from": e.from_state, "to": e.to_state,
                        "integration_date": json_safe(e.integration_date),
                    }
                    for e in w.events
                ],
            }
            for w in storage.get_all(Workflow)
        ],
    }


# ----------------------------------------------------------------------
# Fichiers statiques
# ----------------------------------------------------------------------


def _versioned_index() -> str:
    """index.html dont chaque URL /static/… porte ?v=<empreinte du fichier>.

    Sans cela, après un déploiement, le navigateur combinait la page neuve
    avec un app.js/style.css périmés tirés de son cache (StaticFiles ne pose
    pas de Cache-Control : le navigateur réutilise à l'heuristique). Une
    empreinte PAR FICHIER plutôt qu'un numéro de version global : seul ce qui
    a changé est retéléchargé, les vendors (x6 ≈ 1 Mo) restent en cache.
    Calculé une fois au chargement du module : les fichiers ne bougent pas
    sans redéploiement, donc sans redémarrage du process.
    """
    def stamp(match: re.Match[str]) -> str:
        attr, rel = match.group(1), match.group(2)
        digest = hashlib.sha256((STATIC_DIR / rel).read_bytes()).hexdigest()[:12]
        return f'{attr}="/static/{rel}?v={digest}"'

    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return re.sub(r'(href|src)="/static/([^"?#]+)"', stamp, html)


_INDEX_HTML = _versioned_index()


@app.get("/")
def index() -> HTMLResponse:
    # no-cache = revalider à chaque chargement : la page est minuscule, et
    # c'est elle qui porte les empreintes des fichiers à jour.
    return HTMLResponse(_INDEX_HTML, headers={"Cache-Control": "no-cache"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    # La page déclare /static/favicon.svg, mais certains clients (onglets
    # ouverts sur une autre route, lecteurs de flux, outils) réclament quand
    # même /favicon.ico à la racine : on y sert le même SVG plutôt que de
    # maintenir un .ico binaire en double.
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
