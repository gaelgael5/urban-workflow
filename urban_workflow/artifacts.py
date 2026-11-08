"""Artefacts JSON nommés : ``DEFINE ARTIFACT X 'l' AS @schema USING @script``.

Décision utilisateur du 2026-11-08 : le JSON n'est pas une fin, c'est le
moyen de fournir une **donnée bien formée** à autre chose (exemple : le
corps d'un appel HTTP). On traite d'abord la production de ce JSON :

- un artefact est **déclaré** dans le DSL, avec un nom, un libellé, un JSON
  Schema facultatif (``AS @schema``, comme ``EVENT`` et ``STATE``) et le
  script qui le produit (``USING @script``) ;
- le script est en général une transformation **JSLT** (urban-json,
  langage ``jslt`` du :class:`~urban_workflow.scripts.ScriptRegistry`,
  fichiers ``.jslt``) appliquée au document de contexte décrit par
  :func:`script_document` ;
- il est **consommé** par le chemin ``@artifact.X`` (``@artifact.X.champ``
  pour une partie) dans les arguments d'une action ``EXECUTE`` : il est
  produit au moment où le message de l'action est construit, validé contre
  son schéma, et part dans la chaîne de sorties avec l'action.

Pas de paramètres : le script lit le contexte (choix utilisateur). Le
``TemplateRegistry`` des messages d'action reste un mécanisme séparé.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .clock import WorkflowClock
from .exceptions import ArtifactError, DslSyntaxError, EventSchemaError
from .scripts import CompiledScript, Script, ScriptBinding, ScriptLanguage
from .values import DocumentPath, find_state_instance, state_document

# ----------------------------------------------------------------------
# Document d'entrée des scripts de transformation
# ----------------------------------------------------------------------


def script_document(
    run_ctx: Any,
    params: Mapping[str, Any] | None = None,
    state_name: str = "",
    constants: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Document JSON lu par un script ``jslt`` (``$.…``).

    Mêmes objets, mêmes noms que les chemins du DSL, pour que l'auteur
    raisonne sur un seul modèle :

    - ``IncomingEvent`` — l'événement entrant, format fil (= ``@IncomingEvent``) ;
    - ``state`` — l'instance la plus récente de l'état du bloc qui utilise
      l'artefact (= ``@state``), ``None`` hors d'un ``DEFINE STATE`` ;
    - ``Workflow`` — ``Uuid``, ``ExternalId``, ``CurrentState``,
      ``WorkflowName``, ``Version`` et ses données étendues (= ``@Workflow``) ;
    - ``constants`` — les ``DEFINE CONST`` ; ``params`` — paramètres
      éventuels (vide pour un artefact) ; ``now`` — horloge du moteur, ISO.
    """
    # Imports locaux : le serializer et le templating dépendent du moteur,
    # qui dépend lui-même de ce module de base (cycle au niveau module).
    from .engine.serializer import event_to_document
    from .templating.context import json_safe

    incoming = getattr(run_ctx, "incoming_event", None)
    workflow = getattr(run_ctx, "workflow", None)

    state = None
    if state_name:
        instance = find_state_instance(run_ctx, state_name)
        state = state_document(instance) if instance is not None else {"Name": state_name}

    workflow_doc = None
    if workflow is not None:
        workflow_doc = {
            **(workflow.extended_datas or {}),
            "Uuid": workflow.uuid,
            "ExternalId": workflow.external_id,
            "CurrentState": workflow.current_state,
            "WorkflowName": workflow.workflow_name,
            "Version": workflow.version,
        }

    return json_safe({
        "IncomingEvent": event_to_document(incoming) if incoming is not None else None,
        "state": state,
        "Workflow": workflow_doc,
        "constants": dict(constants or {}),
        "params": dict(params or {}),
        "now": WorkflowClock.now().isoformat(),
    })


# ----------------------------------------------------------------------
# Langage ``jslt``
# ----------------------------------------------------------------------


class JsltLanguage(ScriptLanguage):
    """Transformations urban-json (fichiers ``.jslt``).

    ``functions`` : registre urban-json de fonctions personnalisées
    (``None`` = fonctions intégrées), comme pour le ``TemplateRegistry``.
    """

    name = "jslt"
    extensions = (".jslt",)

    def __init__(self, functions: Any = None) -> None:
        self.functions = functions
        # Compilé une fois par (origine, source) : check() à
        # l'enregistrement puis compile() à chaque site d'appel.
        self._cache: dict[tuple[str, str], Any] = {}

    def template(self, script: Script) -> Any:
        key = (script.where, script.source)
        if key not in self._cache:
            from urban_json import JsltSyntaxError, JsltTemplate

            from .dsl.errors import DslErrorModel

            try:
                self._cache[key] = JsltTemplate.parse(script.source).build()
            except JsltSyntaxError as exc:
                # Même forme que les erreurs du langage expression : la
                # position est DANS le script (origine:ligne:colonne).
                message = str(exc).split(" (ligne ")[0]
                error = DslErrorModel(
                    message=message, filename=script.where,
                    line=exc.line or 1, column=exc.column or 0,
                )
                raise DslSyntaxError(
                    f"1 syntax error(s) in script {script.where!r}: {error}",
                    errors=[error],
                ) from None
        return self._cache[key]

    def check(self, script: Script) -> None:
        self.template(script)

    def compile(self, script: Script, binding: ScriptBinding) -> CompiledScript:
        template = self.template(script)
        build_document = binding.document
        if build_document is None:
            # Un appelant qui ne fournit pas de document (contexte inconnu) :
            # document réduit aux paramètres plutôt qu'un échec.
            def build_document(run_ctx, params):
                return script_document(run_ctx, params, constants=binding.constants)
        functions = self.functions

        def run(run_ctx: Any, params: dict[str, Any]) -> Any:
            return template.transform(build_document(run_ctx, params), functions=functions)

        return run


# ----------------------------------------------------------------------
# Production d'un artefact
# ----------------------------------------------------------------------


def make_producer(
    name: str,
    compiled: CompiledScript,
    where: str,
    schema: Mapping[str, Any] | None,
    schema_ref: str = "",
) -> Callable[[Any], Any]:
    """Callable ``(run_ctx) -> JSON`` : exécute le script puis valide le
    résultat contre le schéma de l'artefact. Lève :class:`ArtifactError`."""
    from .schemas import validate_value
    from .templating.context import json_safe

    def produce(run_ctx: Any) -> Any:
        try:
            value = json_safe(compiled(run_ctx, {}))
        except ArtifactError:
            raise
        except Exception as exc:  # erreur JSLT d'exécution, TypeError…
            raise ArtifactError(
                f"artifact {name!r}: script {where} failed: {exc}"
            ) from exc
        if schema is not None:
            try:
                validate_value(schema, value)
            except EventSchemaError as exc:
                raise ArtifactError(
                    f"artifact {name!r} does not match schema @{schema_ref}: "
                    + " ; ".join(exc.errors),
                    errors=exc.errors,
                ) from None
        return value

    return produce


@dataclass(frozen=True)
class ArtifactPath(DocumentPath):
    """``@artifact.Nom[.partie…]`` : l'artefact produit au moment de la
    résolution (construction du message de l'action).

    Le premier segment est le nom de l'artefact : le document résolu est
    ``{Nom: JSON produit}``, ce qui donne au chemin la même lecture que les
    autres (``@artifact.Requete.client`` = partie ``client``).
    """

    ROOT = "artifact"

    producer: Callable[[Any], Any] | None = field(default=None, compare=False)

    def document(self, ctx: Any) -> Any:
        if self.producer is None or not self.segments:  # pragma: no cover
            return None
        return {self.segments[0]: self.producer(ctx)}


def produce_artifact(
    config: Any,
    name: str,
    scripts: Any,
    run_ctx: Any,
    state_name: str = "",
    constants: Mapping[str, Any] | None = None,
) -> Any:
    """Produit l'artefact ``name`` d'une configuration hors d'une action
    (aperçu, tests, code hôte) : même script, même document, même
    validation que pendant le traitement."""
    declared = config.declared_artifacts[name]
    binding = ScriptBinding(
        owner=f"artifact {name}",
        constants=dict(constants or {}),
        document=lambda ctx, params: script_document(ctx, params, state_name, constants),
    )
    compiled = scripts.compile(declared.script_ref, binding)
    where = scripts.get(declared.script_ref).where
    return make_producer(name, compiled, where, declared.schema, declared.schema_ref)(run_ctx)
