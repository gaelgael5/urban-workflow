"""Artefacts JSON nommés : ``DEFINE ARTIFACT X 'l' AS @schema USING @script``.

Décision utilisateur du 2026-11-08 : le JSON est le moyen de fournir une
donnée bien formée à autre chose (ex. corps d'un appel HTTP). Un artefact
est déclaré dans le DSL, produit par un script (jslt) du ScriptRegistry,
validé par un JSON Schema facultatif, et consommé par ``@artifact.X`` dans
les arguments d'une action.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from urban_workflow import (
    MemoryStorage,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
)
from urban_workflow.artifacts import produce_artifact
from urban_workflow.dsl import parse_config
from urban_workflow.dsl.surface import extract_surface, render_script
from urban_workflow.exceptions import (
    ArtifactError,
    DslSyntaxError,
    DuplicatedArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
    UnknownSchemaError,
    UnknownScriptError,
)
from urban_workflow.outputs import default_memory_output
from urban_workflow.scripts import ScriptRegistry

pytest.importorskip("jsonschema")
from urban_workflow.schemas import SchemaRegistry

WORKFLOW = """
NAME Commandes
DEFINE EVENT Validee 'commande validée';
DEFINE ACTION AppelerApi (TEXT corps, TEXT client) 'appel du service de facturation';
DEFINE CONST  devise 'EUR' 'devise';
DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_requete USING @requete_facture;
INITIALIZE WORKFLOW
    ON EVENT Validee SWITCH Facturee
DEFINE STATE Facturee 'facturée'
    ON ENTER STATE
        EXECUTE AppelerApi(corps = @artifact.RequeteFacture,
                           client = @artifact.RequeteFacture.client)
;
"""

JSLT = """{
    "reference": $.Workflow.ExternalId,
    "client": $.IncomingEvent.Client,
    "montant": $.IncomingEvent.Montant,
    "devise": $.constants.devise,
    "etat": $.state.Name
}"""

SCHEMA = {
    "type": "object",
    "required": ["reference", "client", "montant"],
    "properties": {
        "reference": {"type": "string"},
        "client": {"type": "string"},
        "montant": {"type": "number", "minimum": 0},
        "devise": {"type": "string"},
        "etat": {"type": "string"},
    },
}


def _scripts(source: str = JSLT) -> ScriptRegistry:
    return ScriptRegistry().add_script("requete_facture", source, language="jslt")


def _schemas() -> SchemaRegistry:
    return SchemaRegistry().add_schema("schema_requete", SCHEMA)


def _run(payload: dict, scripts=None, schemas=None, workflow: str = WORKFLOW):
    config = parse_config(
        workflow,
        scripts=scripts if scripts is not None else _scripts(),
        schemas=schemas if schemas is not None else _schemas(),
    )
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    WorkflowEngine(processor).evaluate_event(
        {"Name": "Validee", "Uuid": str(uuid4()), "ExternalId": "CMD-1", **payload}
    )
    (workflow_obj,) = storage.get_all(Workflow)
    return workflow_obj


class TestProduction:
    def test_artifact_is_produced_into_the_action_message(self):
        workflow = _run({"Client": "ACME", "Montant": 120.5})
        (action,) = [a for a in workflow.last_event.actions if a.name == "AppelerApi"]
        arguments = action.execute_message["Body"]["Arguments"]
        assert arguments["corps"] == {
            "reference": "CMD-1", "client": "ACME", "montant": 120.5,
            "devise": "EUR", "etat": "Facturee",
        }
        assert arguments["client"] == "ACME"  # partie de l'artefact

    def test_schema_violation_stops_the_processing(self):
        with pytest.raises(ArtifactError, match="RequeteFacture.*schema_requete.*montant"):
            _run({"Client": "ACME", "Montant": -3})

    def test_missing_required_value_is_reported(self):
        with pytest.raises(ArtifactError, match="client"):
            _run({"Montant": 10})

    def test_without_schema_nothing_is_validated(self):
        workflow_text = WORKFLOW.replace("AS @schema_requete ", "")
        workflow = _run({"Montant": -3}, workflow=workflow_text)
        (action,) = [a for a in workflow.last_event.actions if a.name == "AppelerApi"]
        assert action.execute_message["Body"]["Arguments"]["corps"]["montant"] == -3

    def test_runtime_error_of_the_script_is_an_artifact_error(self):
        broken = _scripts('{ "x": unknownfn($.IncomingEvent.Client) }')
        workflow_text = WORKFLOW.replace("AS @schema_requete ", "").replace(
            ",\n                           client = @artifact.RequeteFacture.client", ""
        ).replace("TEXT corps, TEXT client", "TEXT corps")
        with pytest.raises(ArtifactError, match="requete_facture.*unknownfn"):
            _run({"Client": "ACME"}, scripts=broken, workflow=workflow_text)

    def test_expression_script_can_produce_an_artifact(self):
        scripts = ScriptRegistry().add_script("requete_facture", "@IncomingEvent.Montant * 2")
        workflow_text = WORKFLOW.replace("AS @schema_requete ", "").replace(
            ",\n                           client = @artifact.RequeteFacture.client", ""
        ).replace("TEXT corps, TEXT client", "TEXT corps")
        workflow = _run({"Montant": 21}, scripts=scripts, workflow=workflow_text)
        (action,) = [a for a in workflow.last_event.actions if a.name == "AppelerApi"]
        assert action.execute_message["Body"]["Arguments"]["corps"] == 42

    def test_produce_artifact_outside_an_action(self):
        from urban_workflow.models import IncomingEvent, RunContext

        config = parse_config(WORKFLOW, scripts=_scripts(), schemas=_schemas())
        ctx = RunContext(incoming_event=IncomingEvent(
            name="Validee", extended_datas={"Client": "ACME", "Montant": 1}))
        # Sans workflow, « reference » vaut None : le schéma le refuse, même
        # validation que pendant le traitement.
        with pytest.raises(ArtifactError, match="reference"):
            produce_artifact(config, "RequeteFacture", _scripts(), ctx)
        loose = parse_config(WORKFLOW.replace("AS @schema_requete ", ""), scripts=_scripts())
        value = produce_artifact(loose, "RequeteFacture", _scripts(), ctx,
                                 state_name="Facturee", constants={"devise": "EUR"})
        assert value == {"reference": None, "client": "ACME", "montant": 1,
                         "devise": "EUR", "etat": "Facturee"}


class TestLoadChecks:
    def test_unknown_script_is_positioned_on_using(self):
        with pytest.raises(UnknownScriptError, match=r"x\.wf:7:\d+: artifact 'RequeteFacture'"):
            parse_config(WORKFLOW, scripts=ScriptRegistry(), schemas=_schemas(),
                         filename="x.wf")

    def test_unknown_schema_is_positioned_on_as(self):
        with pytest.raises(UnknownSchemaError, match=r"x\.wf:7:7"):
            parse_config(WORKFLOW, scripts=_scripts(), schemas=SchemaRegistry(),
                         filename="x.wf")

    def test_jslt_syntax_error_is_positioned_in_the_script(self):
        with pytest.raises(DslSyntaxError) as info:
            ScriptRegistry().add_script("r", '{ "a": $.x + }', language="jslt", origin="r.jslt")
        (error,) = info.value.errors
        assert error.filename == "r.jslt" and error.line == 1

    def test_jslt_files_are_loaded_by_extension(self, tmp_path):
        (tmp_path / "requete_facture.jslt").write_text(JSLT, encoding="utf-8")
        scripts = ScriptRegistry().add_directory(tmp_path)
        assert scripts.get("requete_facture").language == "jslt"
        workflow = _run({"Client": "ACME", "Montant": 1}, scripts=scripts)
        assert workflow.current_state == "Facturee"

    def test_unknown_artifact_is_refused(self):
        text = WORKFLOW.replace("corps = @artifact.RequeteFacture,", "corps = @artifact.Autre,")
        with pytest.raises(InvalidArgumentValueError, match="unknown artifact 'Autre'"):
            parse_config(text, scripts=_scripts(), schemas=_schemas())

    def test_unknown_part_is_checked_against_the_schema(self):
        text = WORKFLOW.replace("RequeteFacture.client", "RequeteFacture.clinet")
        with pytest.raises(InvalidArgumentValueError, match="clinet"):
            parse_config(text, scripts=_scripts(), schemas=_schemas())

    def test_artifact_is_refused_in_rule_arguments(self):
        text = """
NAME X
DEFINE EVENT E 'e';
DEFINE RULE R (TEXT v) 'r' AS @r;
DEFINE ARTIFACT A 'a' USING @requete_facture;
INITIALIZE WORKFLOW
    ON EVENT E WHEN R(v = @artifact.A) SWITCH S
DEFINE STATE S 's' ;
"""
        scripts = _scripts().add_script("r", "TRUE")
        with pytest.raises(InvalidArgumentValueError, match="only available in EXECUTE"):
            parse_config(text, scripts=scripts)

    def test_duplicated_artifact(self):
        text = WORKFLOW.replace(
            "DEFINE CONST", "DEFINE ARTIFACT RequeteFacture 'x' USING @requete_facture;\n"
            "DEFINE CONST")
        with pytest.raises(DuplicatedArgumentNameError, match="RequeteFacture"):
            parse_config(text, scripts=_scripts(), schemas=_schemas())

    def test_without_registries_references_are_kept_but_use_is_refused(self):
        with pytest.raises(InvalidMethodReferenceError, match="no ScriptRegistry"):
            parse_config(WORKFLOW)
        unused = WORKFLOW.replace(
            "corps = @artifact.RequeteFacture,", "corps = 'x',"
        ).replace("client = @artifact.RequeteFacture.client", "client = 'y'")
        config = parse_config(unused)
        declared = config.declared_artifacts["RequeteFacture"]
        assert (declared.schema_ref, declared.script_ref, declared.schema) == (
            "schema_requete", "requete_facture", None)


class TestSurface:
    def test_round_trip_keeps_the_artifacts(self):
        model = extract_surface(WORKFLOW)
        (artifact,) = model.artifacts
        assert (artifact.name, artifact.schema_ref, artifact.script) == (
            "RequeteFacture", "schema_requete", "requete_facture")
        text = render_script(model)
        assert "DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'" in text
        assert "AS @schema_requete USING @requete_facture;" in text
        assert render_script(extract_surface(text)) == text
        parse_config(text, scripts=_scripts(), schemas=_schemas())
