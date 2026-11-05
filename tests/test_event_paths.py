"""Arguments ``$.chemin`` : accès JSONPath au document de l'événement entrant.

Extension DSL (comme ``AS``/``UNIQUE``) : ``WHEN Regle(seuil = $.Montant)``
passe à la règle la valeur lue dans le document « format fil » de
l'événement (socle + données métier). Dans un bloc ``ON EVENT X``, le
visiteur sait de quel événement il s'agit : si X a un schéma, un chemin
inconnu est refusé au chargement, positionné.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from urban_workflow import (
    FunctionRegistry,
    MemoryStorage,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import DslSyntaxError, InvalidArgumentValueError
from urban_workflow.outputs import default_memory_output
from urban_workflow.values import EventPath

SCRIPT = """
NAME Demo
DEFINE EVENT DemandeSoumise 'dépôt' AS @schema_DemandeSoumise;
DEFINE RULE Capture (TEXT valeur) 'capture la valeur reçue';
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise WHEN Capture(valeur = {path}) SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""

SCHEMA_YAML = """
type: object
properties:
  Montant: {type: number}
  Client:
    type: object
    properties:
      Pays: {type: string}
  Lignes:
    type: array
    items:
      type: object
      properties:
        Qte: {type: integer}
"""


def _registry(captured: list):
    rules = FunctionRegistry("rule")

    def capture(ctx, valeur):
        captured.append(valeur)
        return True

    rules.add("Capture", capture)
    return rules


def _schemas():
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    from urban_workflow.schemas import SchemaRegistry

    return SchemaRegistry().add_yaml("schema_DemandeSoumise", SCHEMA_YAML)


def _run(path: str, payload_extra: dict, schemas=None) -> list:
    captured: list = []
    script = SCRIPT.format(path=path)
    if schemas is None:
        script = script.replace(" AS @schema_DemandeSoumise", "")
    config = parse_config(script, rules=_registry(captured), schemas=schemas)
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    WorkflowEngine(processor).evaluate_event(
        {"Name": "DemandeSoumise", "Uuid": str(uuid4()), "ExternalId": "DA-1",
         **payload_extra}
    )
    return captured


class TestResolution:
    def test_top_level_business_property(self):
        assert _run("$.Montant", {"Montant": 120}) == [120]

    def test_base_property(self):
        assert _run("$.Name", {}) == ["DemandeSoumise"]
        assert _run("$.ExternalId", {}) == ["DA-1"]

    def test_integration_date_is_visible(self):
        (value,) = _run("$.IntegrationDate", {})
        assert isinstance(value, str) and "T" in value

    def test_nested_index_and_quoted_segments(self):
        payload = {"Client": {"Pays": "FR"}, "Lignes": [{"Qte": 3}, {"Qte": 5}]}
        assert _run("$.Client.Pays", payload) == ["FR"]
        assert _run("$.Lignes[1].Qte", payload) == [5]
        assert _run("$['Client']['Pays']", payload) == ["FR"]

    def test_absent_path_gives_none(self):
        assert _run("$.Absent", {}) == [None]
        assert _run("$.Lignes[9].Qte", {"Lignes": []}) == [None]

    def test_argument_is_an_event_path(self):
        config = parse_config(
            SCRIPT.format(path="$.Lignes[0].Qte").replace(" AS @schema_DemandeSoumise", ""),
            rules=_registry([]),
        )
        assert config.initializers  # le script se charge
        path = EventPath.parse("$.Lignes[0]['Qte']")
        assert path.segments == ("Lignes", 0, "Qte")
        assert str(path) == "$.Lignes[0].Qte"


class TestStaticCheck:
    def test_known_paths_pass_with_schema(self):
        schemas = _schemas()
        assert _run("$.Montant", {"Montant": 1}, schemas) == [1]
        assert _run("$.Client.Pays", {"Montant": 1, "Client": {"Pays": "FR"}}, schemas) == ["FR"]
        assert _run("$.Name", {}, schemas) == ["DemandeSoumise"]  # socle

    def test_unknown_property_is_positioned_error(self):
        schemas = _schemas()
        with pytest.raises(InvalidArgumentValueError, match=r"x\.wf:\d+:\d+.*Montnt"):
            parse_config(
                SCRIPT.format(path="$.Montnt"), rules=_registry([]),
                schemas=schemas, filename="x.wf",
            )

    def test_unknown_nested_property_is_rejected(self):
        schemas = _schemas()
        with pytest.raises(InvalidArgumentValueError, match="Client.Ville"):
            parse_config(
                SCRIPT.format(path="$.Client.Ville"), rules=_registry([]),
                schemas=schemas,
            )

    def test_no_check_without_schema(self):
        assert _run("$.Nimporte", {}) == [None]


class TestSyntax:
    def test_dollar_alone_is_the_whole_document(self):
        (document,) = _run("$", {"Montant": 7})
        assert document["Montant"] == 7 and document["Name"] == "DemandeSoumise"

    def test_malformed_path_is_a_syntax_error(self):
        with pytest.raises(DslSyntaxError):
            parse_config(
                SCRIPT.format(path="$.").replace(" AS @schema_DemandeSoumise", ""),
                rules=_registry([]),
            ).build()
