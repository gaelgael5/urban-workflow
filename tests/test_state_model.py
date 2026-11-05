"""Modélisation des états : ``DEFINE STATE X 'libellé' AS @schema``,
instances d'état à chaque SWITCH, chemins ``@state.…`` et switch viable.

Décisions de cadrage (2026-11-05) :
- un état a un socle non modifiable ``Name``/``Uuid``/``CreationDate`` et
  un schéma métier optionnel ; le calcul des champs métier viendra plus
  tard (ici : modélisation, contrôles, intellisense) ;
- une instance est créée à CHAQUE passage par un SWITCH (y compris vers
  le même état) ;
- ``@state`` = l'état courant, celui du bloc ``DEFINE STATE`` où l'on écrit ;
- un switch n'est valide que si l'état cible offre ensuite une route pour
  l'événement réévalué (RECURSIVE) ; sinon tout se passe comme si ce switch
  n'avait pas été rencontré.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from urban_workflow import (
    FunctionRegistry,
    MemoryStorage,
    Workflow,
    WorkflowClock,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import InvalidArgumentValueError, UnknownSchemaError
from urban_workflow.outputs import default_memory_output

STATE_SCHEMA = "type: object\nproperties:\n  Decision: {type: string}\n"


def _schemas():
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    from urban_workflow.schemas import SchemaRegistry

    return SchemaRegistry().add_yaml("schema_Ouvert", STATE_SCHEMA)


def _rules(captured: list, results: dict | None = None):
    rules = FunctionRegistry("rule")
    results = results if results is not None else {}

    def capture(ctx, valeur):
        captured.append(valeur)
        return True

    def condition(ctx, nom):
        return results.get(nom, False)

    rules.add("Capture", capture)
    rules.add("Condition", condition)
    return rules


def _engine(script: str, rules, schemas=None):
    config = parse_config(script, rules=rules, schemas=schemas)
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage


def _send(engine, name: str, **extra):
    engine.evaluate_event({"Name": name, "Uuid": str(uuid4()), "ExternalId": "K", **extra})


BASE_SCRIPT = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE EVENT Relance 'r';
DEFINE RULE Capture (TEXT valeur) 'capture';
DEFINE RULE Condition (TEXT nom) 'condition';
INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' AS @schema_Ouvert
    ON EVENT Relance WHEN Capture(valeur = {path}) SWITCH Ouvert
;
"""


class TestDsl:
    def test_schema_reference_is_stored_without_registry(self):
        config = parse_config(BASE_SCRIPT.format(path="@state.Name"), rules=_rules([]))
        assert config.states["Ouvert"].schema_ref == "schema_Ouvert"
        assert config.states["Ouvert"].schema is None

    def test_reference_resolved_with_registry(self):
        config = parse_config(
            BASE_SCRIPT.format(path="@state.Name"), rules=_rules([]), schemas=_schemas()
        )
        assert config.states["Ouvert"].schema["properties"]["Decision"] == {"type": "string"}

    def test_unknown_reference_is_positioned_error(self):
        schemas = _schemas()
        script = BASE_SCRIPT.format(path="@state.Name").replace(
            "AS @schema_Ouvert", "AS @inconnu"
        )
        with pytest.raises(UnknownSchemaError, match=r"x\.wf:\d+:\d+.*inconnu"):
            parse_config(script, rules=_rules([]), schemas=schemas, filename="x.wf")

    def test_state_path_in_initialize_is_rejected(self):
        script = BASE_SCRIPT.format(path="@state.Name").replace(
            "ON EVENT Ouverture SWITCH Ouvert",
            "ON EVENT Ouverture WHEN Capture(valeur = @state.Name) SWITCH Ouvert",
        )
        with pytest.raises(InvalidArgumentValueError, match=r"x\.wf:\d+:\d+.*@state"):
            parse_config(script, rules=_rules([]), filename="x.wf")

    def test_unknown_state_property_is_rejected_with_schema(self):
        with pytest.raises(InvalidArgumentValueError, match="Decisoin"):
            parse_config(
                BASE_SCRIPT.format(path="@state.Decisoin"), rules=_rules([]),
                schemas=_schemas(),
            )

    def test_base_and_business_state_properties_pass(self):
        for path in ("@state.Name", "@state.Uuid", "@state.CreationDate", "@state.Decision"):
            parse_config(BASE_SCRIPT.format(path=path), rules=_rules([]), schemas=_schemas())


class TestStatePathResolution:
    def test_state_path_reads_the_current_instance(self):
        captured: list = []
        engine, storage = _engine(BASE_SCRIPT.format(path="@state.Name"), _rules(captured))
        _send(engine, "Ouverture")
        _send(engine, "Relance")
        assert captured == ["Ouvert"]

    def test_uuid_and_creation_date_come_from_the_instance(self):
        from datetime import datetime, timezone

        captured: list = []
        engine, storage = _engine(BASE_SCRIPT.format(path="@state"), _rules(captured))
        entry = datetime(2026, 11, 5, 8, 0, tzinfo=timezone.utc)
        with WorkflowClock.frozen(entry):
            _send(engine, "Ouverture")
        _send(engine, "Relance")
        (document,) = captured
        instance = storage.get_by(Workflow, "K", "external_id")[0].states[0]
        assert document["Name"] == "Ouvert"
        assert document["Uuid"] == str(instance.uuid)
        assert document["CreationDate"] == entry.isoformat()
        assert document["EventId"] == str(instance.event_id)

    def test_state_references_the_event_that_created_it(self):
        engine, storage = _engine(BASE_SCRIPT.format(path="@state.Name"), _rules([]))
        uuid = str(uuid4())
        engine.evaluate_event({"Name": "Ouverture", "Uuid": uuid, "ExternalId": "K"})
        (instance,) = storage.get_by(Workflow, "K", "external_id")[0].states
        assert str(instance.event_id) == uuid

    def test_one_event_two_workflows_each_its_own_state(self):
        # Le même événement crée deux workflows (deux configurations) : chacun
        # a son instance d'état, toutes deux référençant le même événement.
        script_b = BASE_SCRIPT.format(path="@state.Name").replace("NAME Demo", "NAME Autre")
        configs = WorkflowsConfig()
        configs.add_document(parse_config(BASE_SCRIPT.format(path="@state.Name"), rules=_rules([])))
        configs.add_document(parse_config(script_b, rules=_rules([])))
        storage = MemoryStorage()
        processor = WorkflowProcessor(configs, WorkflowFactory())
        processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
            Workflow, key, "external_id"
        )
        processor.output_actions = default_memory_output(storage)
        uuid = str(uuid4())
        WorkflowEngine(processor).evaluate_event(
            {"Name": "Ouverture", "Uuid": uuid, "ExternalId": "K"}
        )
        workflows = storage.get_by(Workflow, "K", "external_id")
        assert sorted(w.workflow_name for w in workflows) == ["Autre", "Demo"]
        for workflow in workflows:
            (instance,) = workflow.states
            assert str(instance.event_id) == uuid


class TestInstances:
    def test_each_switch_creates_an_instance_even_to_the_same_state(self):
        engine, storage = _engine(BASE_SCRIPT.format(path="@state.Name"), _rules([]))
        _send(engine, "Ouverture")
        _send(engine, "Relance")  # Ouvert → Ouvert
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Ouvert", "Ouvert"]
        assert workflow.states[0].uuid != workflow.states[1].uuid

    def test_recursive_chain_creates_one_instance_per_switch(self):
        script = """
NAME Demo
DEFINE EVENT Depot 'd';
INITIALIZE WORKFLOW
    ON EVENT Depot RECURSIVE SWITCH Tri
DEFINE STATE Tri 'tri'
    ON EVENT Depot SWITCH Fini
;
DEFINE STATE Fini 'fini' ;
"""
        engine, storage = _engine(script, _rules([]))
        _send(engine, "Depot")
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Tri", "Fini"]
        assert workflow.current_state == "Fini"

    def test_no_switch_no_instance(self):
        script = BASE_SCRIPT.format(path="@state.Name").replace(
            "WHEN Capture(valeur = @state.Name)", "WHEN Condition(nom = 'jamais')"
        )
        engine, storage = _engine(script, _rules([]))
        _send(engine, "Ouverture")
        _send(engine, "Relance")  # aucune branche ne passe
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Ouvert"]


ROUTING_SCRIPT = """
NAME Demo
DEFINE EVENT Depot 'd';
DEFINE RULE Condition (TEXT nom) 'condition';
INITIALIZE WORKFLOW
    ON EVENT Depot RECURSIVE SWITCH Tri
DEFINE STATE Tri 'tri'
    ON EVENT Depot
        WHEN Condition(nom = 'a') SWITCH A
        WHEN Condition(nom = 'b') SWITCH B
;
DEFINE STATE A 'a' ;
DEFINE STATE B 'b' ;
"""


class TestViableSwitch:
    def test_dead_end_rejects_the_whole_chain(self):
        engine, storage = _engine(ROUTING_SCRIPT, _rules([], {}))
        _send(engine, "Depot")
        assert storage.get_all(Workflow) == []

    def test_route_found_creates_the_workflow(self):
        engine, storage = _engine(ROUTING_SCRIPT, _rules([], {"b": True}))
        _send(engine, "Depot")
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Tri", "B"]

    def test_target_without_handler_is_viable(self):
        script = ROUTING_SCRIPT.replace(
            "    ON EVENT Depot\n        WHEN Condition(nom = 'a') SWITCH A\n"
            "        WHEN Condition(nom = 'b') SWITCH B\n", ""
        )
        engine, storage = _engine(script, _rules([], {}))
        _send(engine, "Depot")
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Tri"]

    def test_no_lookahead_without_recursive(self):
        # Sans RECURSIVE, l'événement n'est pas réévalué dans Tri : la cible
        # n'a pas à offrir de route pour CET événement.
        engine, storage = _engine(ROUTING_SCRIPT.replace(" RECURSIVE", ""), _rules([], {}))
        _send(engine, "Depot")
        workflow = storage.get_by(Workflow, "K", "external_id")[0]
        assert [s.name for s in workflow.states] == ["Tri"]


class TestBaseStateSchema:
    def test_base_fields_are_read_only(self):
        from urban_workflow.schemas import BASE_STATE_SCHEMA

        assert set(BASE_STATE_SCHEMA["properties"]) == {
            "Name", "Uuid", "CreationDate", "EventId",
        }
        for prop in BASE_STATE_SCHEMA["properties"].values():
            assert prop["readOnly"] is True
