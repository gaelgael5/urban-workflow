"""API du playground : analyse (diagnostics + symboles) et simulation.

Deux endpoints :

- ``POST /api/analyze`` — analyse un script avec les règles paramétrées ;
  retourne les erreurs **positionnées** (syntaxe et sémantique), les
  symboles pour l'intellisense (événements, règles, actions, constantes,
  états) et un résumé structurel de la configuration ;
- ``POST /api/simulate`` — rejoue une suite d'événements sur le script
  (moteur complet en mémoire) et retourne états, actions poussées et
  journal fonctionnel.

Les règles métier de code n'existant pas côté navigateur, le panneau de
paramétrage les déclare (nom, paramètres typés, résultat simulé) ; le
serveur fabrique des callables à la signature exacte pour que la
validation des appels ``WHEN`` soit la vraie. Les règles qui référencent
un script (``DEFINE RULE … AS @nom``) sont, elles, évaluées pour de vrai :
les scripts (vue « Scripts ») sont envoyés avec chaque requête et chargés
dans un ``ScriptRegistry``.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
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
from urban_workflow.scripts import Script, ScriptLanguage, ScriptRegistry
from urban_workflow.templating.context import json_safe

from .layout import LayoutDirectory, LayoutError
from .python_scripts import PYTHON_SCRIPTS
from .python_scripts import describe as describe_python_scripts

STATIC_DIR = Path(__file__).parent / "static"

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]*$")
_POSITIONED = re.compile(r"^(?:([^:\n]*):)?(\d+):(\d+):\s*(.*)$", re.DOTALL)
# « … (in rule 'R' called|declared at playground:12:8) » : endroit du
# workflow où le script est utilisé (appel, ou référence AS @ contrôlée).
_CALLED_AT = re.compile(
    r"\(in (?:rule|artifact) '([^']*)' (?:called|declared) at "
    r"(?:[^:\n]*:)?(\d+):(\d+)\)\s*$"
)
# Langages qu'on accepte du navigateur : des langages de données, sans
# exécution de code arbitraire (jslt = transformation JSON urban-json).
_BROWSER_LANGUAGES = ("expression", "jslt")

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


class ScriptSetting(BaseModel):
    """Un script (méthode d'une règle ``AS @nom``) édité dans la vue Scripts."""

    name: str
    language: str = "expression"
    source: str = ""


class AnalyzeRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)
    scripts: list[ScriptSetting] = Field(default_factory=list)


class SimulateRequest(BaseModel):
    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)
    scripts: list[ScriptSetting] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


class ArtifactPreviewRequest(BaseModel):
    """Aperçu d'un artefact : le JSON que produirait son script pour un
    événement d'exemple, dans l'état indiqué."""

    script: str
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)
    scripts: list[ScriptSetting] = Field(default_factory=list)
    artifact: str
    event: dict[str, Any] = Field(default_factory=dict)
    state: str = ""


class DiagramRequest(BaseModel):
    script: str


class GenerateRequest(BaseModel):
    """Modèle de surface (vue diagramme) → script DSL + validation."""

    model: dict[str, Any]
    rules: list[RuleSetting] = Field(default_factory=list)
    schemas: list[SchemaSetting] = Field(default_factory=list)
    scripts: list[ScriptSetting] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Règles simulées
# ----------------------------------------------------------------------


def _build_registry(settings: list[RuleSetting], script: str = "") -> FunctionRegistry:
    """Fabrique des callables à la signature exacte des règles paramétrées.

    Les règles qui référencent un script (``DEFINE RULE … AS @nom``) sont
    évaluées par le moteur : leur entrée éventuelle dans le panneau est
    ignorée, sinon le visiteur refuserait « script ET code »."""
    registry = FunctionRegistry("rule")
    with_script = {name for name, _ in _RE_RULE_SCRIPT.findall(script)}
    for setting in settings:
        if not _IDENTIFIER.match(setting.name) or setting.name in with_script:
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


class _InvalidScript(ScriptLanguage):
    """Tient la place d'un script en erreur de syntaxe : son erreur est
    déjà signalée (dans la vue Scripts) ; sans cette place, chaque règle qui
    le référence ajouterait un faux « script inconnu », et l'analyse du
    workflow s'arrêterait là."""

    name = "invalide"

    def compile(self, script: Script, binding):
        return lambda run_ctx, params: False


def _build_script_registry(
    settings: list[ScriptSetting],
) -> tuple[ScriptRegistry, list[dict[str, Any]]]:
    """Charge les scripts de la vue Scripts ; erreurs positionnées DANS
    chaque script (champ ``script``). Toujours un registre : dans le
    playground, une référence ``AS @nom`` est toujours vérifiée.

    Les fonctions Python du playground (``python_scripts``) sont
    enregistrées d'abord, comme le ferait une application : leurs noms sont
    réservés, et le navigateur ne peut écrire que des scripts ``expression``
    — aucun code Python venu du navigateur n'est exécuté."""
    registry = ScriptRegistry()
    registry.register_language(_InvalidScript())
    for name, func in PYTHON_SCRIPTS.items():
        registry.add_function(name, func)
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for setting in settings:
        if not setting.name or setting.name in seen:
            continue
        seen.add(setting.name)
        if setting.name in PYTHON_SCRIPTS:
            errors.append({**_error_entry(
                f"@{setting.name} est une fonction Python fournie par le playground : "
                "nom réservé, choisir un autre nom"), "script": setting.name})
            continue
        if setting.language not in _BROWSER_LANGUAGES:
            # Avant : add_script(language="python") levait un TypeError non
            # rattrapé (erreur 500). Le Python s'enregistre côté serveur.
            errors.append({**_error_entry(
                f"langage {setting.language!r} non modifiable dans le playground : "
                "seuls les scripts « expression » et « jslt » s'écrivent ici (les fonctions "
                "Python sont enregistrées par l'application)"), "script": setting.name})
            registry.add(Script(setting.name, "invalide", origin=setting.name))
            continue
        try:
            # origin = nom : les positions s'écrivent « nom:ligne:col ».
            registry.add_script(
                setting.name, setting.source, setting.language, origin=setting.name
            )
        except DslSyntaxError as exc:
            errors.extend(
                {**_error_entry(e.message, e.line, e.column), "script": setting.name}
                for e in exc.errors
            )
            registry.add(Script(setting.name, "invalide", origin=setting.name))
        except WorkflowError as exc:
            errors.append({**_error_entry(str(exc)), "script": setting.name})
            registry.add(Script(setting.name, "invalide", origin=setting.name))
    return registry, errors


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

    problems: list[str] = []
    for setting in settings:
        try:
            registry.add_yaml(setting.name, setting.yaml)
        except Exception as exc:
            problems.append(f"schéma {setting.name!r} : {exc}")
    return registry, problems


def _schema_clash_problems(symbols: dict[str, Any], registry) -> list[str]:
    """Schémas métier qui redéfinissent un champ du socle de leur objet.

    Le socle est posé par le moteur (événement : validé sur TOUT événement ;
    état : posé au SWITCH) : un schéma métier qui le redéfinit ajouterait
    une contrainte contradictoire (Uuid entier vs format uuid) que plus rien
    ne pourrait satisfaire. Le socle dépend de l'USAGE du schéma — référencé
    par un DEFINE EVENT ou un DEFINE STATE — d'où un contrôle après lecture
    du script, côté serveur, pour que l'éditeur visuel ne soit pas la seule
    barrière.
    """
    from urban_workflow.schemas import BASE_EVENT_SCHEMA, BASE_STATE_SCHEMA

    if registry is None:
        return []
    usages = [
        (_schema_refs(symbols, "event"), BASE_EVENT_SCHEMA, "des événements"),
        (_schema_refs(symbols, "state"), BASE_STATE_SCHEMA, "des états"),
    ]
    problems: list[str] = []
    for refs, base, owner in usages:
        for ref in sorted({r for r in refs.values() if r}):
            if ref not in registry:
                continue
            clash = sorted(set(base["properties"]) & set(registry.get(ref).get("properties") or {}))
            if clash:
                problems.append(
                    f"schéma {ref!r} : {', '.join(clash)} appartien(nen)t au "
                    f"socle commun {owner} et ne se redéfini(ssen)t pas dans "
                    "un schéma métier"
                )
    return problems


def _schema_refs(symbols: dict[str, Any], kind: str) -> dict[str, str]:
    """``{nom: schema_ref}`` des événements ou des états — détails du
    visiteur si le script compile, sinon repli regex (pendant la frappe)."""
    details = symbols.get(f"{kind}_details") or []
    if details:
        return {d["name"]: d.get("schema_ref", "") for d in details}
    names = symbols.get("events" if kind == "event" else "states", [])
    refs = {n: "" for n in names if not n.startswith(("$", "__"))}
    refs.update(symbols.get(f"{kind}_schema_refs", {}))
    return refs


# ----------------------------------------------------------------------
# Extraction de symboles (repli regex quand le script ne compile pas)
# ----------------------------------------------------------------------

_RE_EVENT = re.compile(r"\bDEFINE\s+EVENT\s+(\w+)", re.IGNORECASE)
# DEFINE EVENT nom 'libellé'? AS @schema : sert au repli quand le script ne
# compile pas — cas permanent PENDANT la frappe (« seuil = $. »), qui est
# justement le moment où l'intellisense des chemins $ doit connaître le
# schéma de l'événement.
_RE_EVENT_SCHEMA = re.compile(
    r"\bDEFINE\s+EVENT\s+(\w+)(?:\s*'(?:[^']|'')*')?\s+AS\s+@(\w+)", re.IGNORECASE
)
_RE_STATE_SCHEMA = re.compile(
    r"\bDEFINE\s+STATE\s+(\w+)(?:\s*'(?:[^']|'')*')?\s+AS\s+@(\w+)", re.IGNORECASE
)
_RE_RULE = re.compile(r"\bDEFINE\s+RULE\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE)
_RE_ACTION = re.compile(r"\bDEFINE\s+ACTION\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE)
# DEFINE RULE|ACTION nom (…) 'libellé'? AS @script (repli pendant la frappe).
_RE_RULE_SCRIPT = re.compile(
    r"\bDEFINE\s+RULE\s+(\w+)\s*\([^)]*\)\s*(?:'(?:[^']|'')*')?\s*AS\s+@([\w.]+)"
)
_RE_ACTION_SCRIPT = re.compile(
    r"\bDEFINE\s+ACTION\s+(\w+)\s*\([^)]*\)\s*(?:'(?:[^']|'')*')?\s*AS\s+@([\w.]+)"
)
# DEFINE ARTIFACT nom 'libellé'? (AS @schema)? USING @script (repli).
_RE_ARTIFACT = re.compile(
    r"\bDEFINE\s+ARTIFACT\s+(\w+)\s*(?:'((?:[^']|'')*)')?\s*"
    r"(?:AS\s+@([\w.]+)\s*)?(?:USING\s+@([\w.]+))?"
)
_RE_CONST = re.compile(r"\bDEFINE\s+CONST\s+(\w+)", re.IGNORECASE)
_RE_STATE = re.compile(r"\bDEFINE\s+STATE\s+(\w+)", re.IGNORECASE)
_RE_PARAM = re.compile(r"(TEXT|INTEGER|DECIMAL)\s+(\w+)", re.IGNORECASE)


def _params_from_text(text: str) -> list[dict[str, str]]:
    return [
        {"name": name, "type": kind.upper()}
        for kind, name in _RE_PARAM.findall(text or "")
    ]


def _symbols_from_text(script: str) -> dict[str, Any]:
    rule_scripts = dict(_RE_RULE_SCRIPT.findall(script))
    action_scripts = dict(_RE_ACTION_SCRIPT.findall(script))
    return {
        "events": sorted(set(_RE_EVENT.findall(script))),
        "rules": [
            {
                "name": name,
                "params": _params_from_text(params),
                "script": rule_scripts.get(name, ""),
            }
            for name, params in _RE_RULE.findall(script)
        ],
        "actions": [
            {
                "name": name,
                "params": _params_from_text(params),
                "script": action_scripts.get(name, ""),
            }
            for name, params in _RE_ACTION.findall(script)
        ],
        "artifacts": [
            {"name": name, "label": label.replace("''", "'"), "schema_ref": schema,
             "script": using}
            for name, label, schema, using in _RE_ARTIFACT.findall(script)
        ],
        "constants": sorted(set(_RE_CONST.findall(script))),
        "states": sorted(set(_RE_STATE.findall(script))),
        "event_schema_refs": dict(_RE_EVENT_SCHEMA.findall(script)),
        "state_schema_refs": dict(_RE_STATE_SCHEMA.findall(script)),
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
                # Méthode référencée (règle évaluée par le moteur) : le
                # panneau Paramétrage n'a pas à la simuler.
                "script": d.script_ref,
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
        "artifacts": [
            {"name": a.name, "label": a.label, "schema_ref": a.schema_ref,
             "script": a.script_ref}
            for a in config.declared_artifacts.values()
        ],
        "constants": [
            {"name": c.key, "value": c.value, "comment": c.comment}
            for c in visitor.constants.values()
        ],
        "states": sorted(config.states),
        "state_details": [
            {"name": s.name, "label": s.label, "schema_ref": s.schema_ref}
            for s in config.states.values()
        ],
    }


# ----------------------------------------------------------------------
# Erreurs positionnées
# ----------------------------------------------------------------------


def _error_entry(message: str, line: int = 1, column: int = 0) -> dict[str, Any]:
    return {"line": line, "column": column, "message": message, "severity": "error"}


def _positioned(exc: WorkflowError, scripts: set[str] = frozenset()) -> list[dict[str, Any]]:
    """Retrouve ``ligne:colonne`` dans le message des erreurs du visiteur.

    Une erreur positionnée dans un SCRIPT (``nom:ligne:col``) donne deux
    entrées : l'une dans le script (vue Scripts), l'autre dans l'éditeur au
    site d'appel quand il est cité — sinon le workflow serait « en erreur »
    sans rien de souligné."""
    match = _POSITIONED.match(str(exc))
    if not match:
        return [_error_entry(str(exc))]
    origin, line, column, message = match.groups()
    if origin not in scripts:
        return [_error_entry(message, int(line), int(column))]
    entries = [{**_error_entry(message, int(line), int(column)), "script": origin}]
    called = _CALLED_AT.search(message)
    short = _CALLED_AT.sub("", message).strip()
    if called:
        entries.append(_error_entry(
            f"script @{origin} : {short}", int(called.group(2)), int(called.group(3))
        ))
    else:
        entries.append(_error_entry(f"script @{origin} : {short}"))
    return entries


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


def _object_properties(
    symbols: dict[str, Any], schema_registry, kind: str, base: dict[str, Any]
) -> dict[str, list]:
    """Pour chaque événement (ou état) : propriétés de son schéma métier
    D'ABORD — ce sont elles qu'on cherche en tapant le chemin — puis le
    socle, identique pour tous."""
    result: dict[str, list] = {}
    for name, ref in _schema_refs(symbols, kind).items():
        properties: dict[str, Any] = {}
        if ref and schema_registry is not None and ref in schema_registry:
            properties.update(schema_registry.get(ref).get("properties") or {})
        for key, value in base["properties"].items():
            properties.setdefault(key, value)
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


def _layout_directory() -> LayoutDirectory | None:
    # Lu à chaque requête (pas au chargement du module) : la configuration
    # suit l'environnement du processus, et les tests la font varier.
    path = os.environ.get("PLAYGROUND_LAYOUT_DIR", "").strip()
    return LayoutDirectory(path) if path else None


@app.get("/api/layout/{workflow}")
def get_layout(workflow: str) -> dict[str, Any]:
    """Mise en page enregistrée du diagramme d'un workflow.

    ``enabled: false`` quand aucun répertoire n'est configuré : le
    navigateur garde alors ses positions dans son propre stockage.
    """
    directory = _layout_directory()
    if directory is None:
        return {"enabled": False, "layout": None}
    try:
        return {"enabled": True, "layout": directory.load(workflow)}
    except (LayoutError, ValueError) as exc:  # nom refusé ou fichier corrompu
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.put("/api/layout/{workflow}")
def put_layout(workflow: str, data: dict[str, Any] = Body(...)) -> dict[str, Any]:
    directory = _layout_directory()
    if directory is None:
        raise HTTPException(status_code=404, detail="no layout directory configured "
                            "(PLAYGROUND_LAYOUT_DIR)")
    try:
        return {"enabled": True, "layout": directory.save(workflow, data)}
    except LayoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/api/base-state-schema")
def base_state_schema() -> dict[str, Any]:
    # Source unique du socle des états (vue « États »).
    from urban_workflow.schemas import BASE_STATE_SCHEMA

    return BASE_STATE_SCHEMA


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    summary: dict[str, Any] | None = None
    symbols = _symbols_from_text(request.script)

    schema_registry, schema_problems = _build_schema_registry(request.schemas)
    errors.extend(_error_entry(problem) for problem in schema_problems)
    script_registry, script_errors = _build_script_registry(request.scripts)

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    for error in parser.errors:
        errors.append(_error_entry(error.message, error.line, error.column))

    if not errors:
        visitor = WorkflowConfigVisitor(
            rules=_build_registry(request.rules, request.script),
            filename="playground",
            schemas=schema_registry,
            scripts=script_registry,
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
            errors.extend(_positioned(exc, set(script_registry.names())))

    # Les erreurs des scripts eux-mêmes ne bloquent pas l'analyse du
    # workflow (le script en erreur tient sa place) : ajoutées après.
    errors.extend(script_errors)
    symbols["schemas"] = sorted(s.name for s in request.schemas)
    symbols["scripts"] = [
        {"name": s.name, "language": s.language} for s in request.scripts if s.name
    ]
    symbols["python_scripts"] = describe_python_scripts()
    symbols["jslt_functions"] = _jslt_functions()
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
    from urban_workflow.schemas import BASE_EVENT_SCHEMA, BASE_STATE_SCHEMA

    symbols["event_properties"] = _object_properties(
        symbols, schema_registry, "event", BASE_EVENT_SCHEMA
    )
    symbols["base_paths"] = _flatten_schema_paths(BASE_EVENT_SCHEMA["properties"])
    symbols["state_properties"] = _object_properties(
        symbols, schema_registry, "state", BASE_STATE_SCHEMA
    )
    symbols["base_state_paths"] = _flatten_schema_paths(BASE_STATE_SCHEMA["properties"])
    symbols.setdefault("state_details", [])
    # Parties d'artefact proposées après « @artifact.Nom. » (schéma résolu).
    symbols["artifact_properties"] = {
        a["name"]: _flatten_schema_paths(
            schema_registry.get(a["schema_ref"]).get("properties") or {}
        )
        if a.get("schema_ref") and schema_registry is not None
        and a["schema_ref"] in schema_registry else []
        for a in symbols.get("artifacts", [])
    }

    clashes = _schema_clash_problems(symbols, schema_registry)
    errors.extend(_error_entry(problem) for problem in clashes)

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
            script=script, rules=request.rules, schemas=request.schemas,
            scripts=request.scripts,
        )
    )
    return {
        "ok": analysis["ok"],
        "script": script,
        "errors": analysis["errors"],
        "summary": analysis["summary"],
    }


_JSLT_FUNCTIONS: list[dict[str, Any]] | None = None


def _jslt_functions() -> list[dict[str, Any]]:
    """Fonctions intégrées d'urban-json, pour la complétion des scripts
    jslt (lue une fois : le catalogue ne change pas en cours de route)."""
    global _JSLT_FUNCTIONS
    if _JSLT_FUNCTIONS is None:
        from urban_json import default_registry

        catalogue = []
        for name in sorted(default_registry.names()):
            info = default_registry.describe(name)
            catalogue.append({
                "name": name,
                "params": [p.name for p in info.parameters],
                "returns": info.returns or "",
                "doc": info.description or "",
            })
        _JSLT_FUNCTIONS = catalogue
    return _JSLT_FUNCTIONS


@app.post("/api/artifact-preview")
def artifact_preview(request: ArtifactPreviewRequest) -> dict[str, Any]:
    """Produit un artefact sur un événement d'exemple (vue Scripts).

    Même script, même document et même validation que pendant le
    traitement ; le workflow est simulé (ExternalId de l'événement, état
    demandé fraîchement créé) pour que ``$.Workflow``/``$.state`` aient un
    contenu réaliste."""
    from urban_workflow.artifacts import produce_artifact
    from urban_workflow.clock import WorkflowClock
    from urban_workflow.engine.serializer import parse_incoming_event
    from urban_workflow.models import RunContext, StateInstance

    schema_registry, schema_problems = _build_schema_registry(request.schemas)
    if schema_problems:
        return {"ok": False, "error": " ; ".join(schema_problems)}
    script_registry, script_errors = _build_script_registry(request.scripts)
    if any(e.get("script") for e in script_errors):
        first = script_errors[0]
        return {"ok": False, "error": f"script @{first['script']} : {first['message']}"}
    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    try:
        parser.check()
        visitor = WorkflowConfigVisitor(
            rules=_build_registry(request.rules, request.script), filename="playground",
            schemas=schema_registry, scripts=script_registry,
        )
        config = parser.visit(visitor)
        if request.artifact not in config.declared_artifacts:
            return {"ok": False, "error": f"artefact {request.artifact!r} non déclaré"}
        incoming = parse_incoming_event(request.event)
        workflow = Workflow(
            workflow_name=config.name, version=config.version,
            external_id=incoming.external_id or "",
        )
        ctx = RunContext(workflow=workflow, incoming_event=incoming)
        if request.state:
            ctx.pending_states.append(StateInstance(
                name=request.state, creation_date=WorkflowClock.now(),
                event_id=incoming.uuid,
            ))
        constants = {k: c.value for k, c in visitor.constants.items()}
        value = produce_artifact(
            config, request.artifact, script_registry, ctx,
            state_name=request.state, constants=constants,
        )
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc),
                "errors": [str(e) for e in getattr(exc, "errors", None) or []]}
    return {"ok": True, "value": json_safe(value)}


@app.post("/api/simulate")
def simulate(request: SimulateRequest) -> dict[str, Any]:
    registry = _build_registry(request.rules, request.script)

    schema_registry, schema_problems = _build_schema_registry(request.schemas)
    if schema_problems:
        return {"ok": False, "error": " ; ".join(schema_problems), "steps": []}
    script_registry, script_errors = _build_script_registry(request.scripts)
    if script_errors:
        problems = [f"script @{e['script']} {e['line']}:{e['column']} : {e['message']}"
                    for e in script_errors]
        return {"ok": False, "error": " ; ".join(problems), "steps": []}

    parser = WorkflowScriptParser.parse_string(request.script, filename="playground")
    try:
        parser.check()
        config = parser.visit(
            WorkflowConfigVisitor(
                rules=registry, filename="playground", schemas=schema_registry,
                scripts=script_registry,
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
                # Une instance par SWITCH, chacune référençant l'événement
                # qui l'a créée.
                "states": [
                    {
                        "name": s.name, "uuid": str(s.uuid),
                        "creation_date": json_safe(s.creation_date),
                        "event_id": str(s.event_id) if s.event_id else None,
                    }
                    for s in w.states
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
