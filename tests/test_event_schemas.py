"""Schémas d'événements : extension DSL ``AS @schema`` + SchemaRegistry.

La partie grammaire (référence stockée) fonctionne sans dépendance ;
le chargement YAML et la validation nécessitent l'extra ``[schemas]``
(PyYAML + jsonschema) et sont skippés proprement sans eux.

Note : le branchement moteur (validation à l'entrée + anti-doublon) est
en attente du choix du mécanisme de définition des clés d'unicité.
"""

from __future__ import annotations

import pytest

from urban_workflow import FunctionRegistry
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import (
    DuplicatedArgumentNameError,
    EventSchemaError,
    UnknownSchemaError,
)

SCRIPT = """
NAME Demo
DEFINE EVENT DemandeSoumise 'une demande est déposée'
    AS @schema_DemandeSoumise UNIQUE (ExternalId, Montant);
DEFINE EVENT Simple 'sans schéma';
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""


class TestDslReference:
    def test_as_reference_is_stored_without_registry(self):
        # Mode permissif (ex. playground) : la référence est conservée,
        # aucune résolution ni dépendance exigée.
        config = parse_config(SCRIPT, rules=FunctionRegistry("rule"))
        declared = config.declared_events["DemandeSoumise"]
        assert declared.schema_ref == "schema_DemandeSoumise"
        assert declared.schema is None
        # UNIQUE est du pur DSL : résolu même sans registre de schémas.
        assert declared.dedup_keys == ["ExternalId", "Montant"]
        assert config.declared_events["Simple"].schema_ref == ""

    def test_duplicated_unique_property_is_positioned_error(self):
        script = SCRIPT.replace(
            "UNIQUE (ExternalId, Montant)", "UNIQUE (ExternalId, ExternalId)"
        )
        from urban_workflow.exceptions import DuplicatedArgumentNameError

        with pytest.raises(
            DuplicatedArgumentNameError, match=r"x\.wf:\d+:\d+.*ExternalId"
        ):
            parse_config(script, rules=FunctionRegistry("rule"), filename="x.wf")

    def test_unknown_reference_is_positioned_error(self):
        yaml = pytest.importorskip("yaml")  # noqa: F841
        from urban_workflow.schemas import SchemaRegistry

        with pytest.raises(UnknownSchemaError, match=r"test\.wf:\d+:\d+"):
            parse_config(
                SCRIPT,
                rules=FunctionRegistry("rule"),
                filename="test.wf",
                schemas=SchemaRegistry(),
            )

    def test_reference_resolved_with_registry(self):
        pytest.importorskip("yaml")
        from urban_workflow.schemas import SchemaRegistry

        registry = SchemaRegistry().add_yaml(
            "schema_DemandeSoumise",
            """
            title: DemandeSoumise
            type: object
            properties:
              Montant: {type: number}
            required: [Montant]
            """,
        )
        config = parse_config(SCRIPT, rules=FunctionRegistry("rule"), schemas=registry)
        declared = config.declared_events["DemandeSoumise"]
        assert declared.schema["title"] == "DemandeSoumise"
        assert declared.dedup_keys == ["ExternalId", "Montant"]  # vient du DSL


class TestSchemaRegistry:
    @pytest.fixture(autouse=True)
    def _requires_yaml(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")

    def make_registry(self):
        from urban_workflow.schemas import SchemaRegistry

        return SchemaRegistry().add_yaml(
            "schema_DemandeSoumise",
            """
            title: DemandeSoumise
            type: object
            properties:
              Montant: {type: number, minimum: 0}
              Canal: {type: string, enum: [web, mail]}
            required: [Montant]
            """,
        )

    def test_load_from_directory(self, tmp_path):
        from urban_workflow.schemas import SchemaRegistry

        (tmp_path / "schema_Ping.yaml").write_text(
            "type: object\nproperties: {Qui: {type: string}}", encoding="utf-8"
        )
        registry = SchemaRegistry().add_directory(tmp_path)
        assert "schema_Ping" in registry
        assert registry.get("schema_Ping")["type"] == "object"

    def test_duplicate_name_rejected(self):
        registry = self.make_registry()
        with pytest.raises(DuplicatedArgumentNameError):
            registry.add_yaml("schema_DemandeSoumise", "type: object")

    def test_valid_document_passes(self):
        registry = self.make_registry()
        registry.validate(
            "schema_DemandeSoumise",
            {"Name": "DemandeSoumise", "ExternalId": "DA-1", "Montant": 120},
        )

    def test_invalid_payload_lists_errors(self):
        registry = self.make_registry()
        with pytest.raises(EventSchemaError) as excinfo:
            registry.validate(
                "schema_DemandeSoumise",
                {"Name": "DemandeSoumise", "Montant": "beaucoup", "Canal": "pigeon"},
            )
        message = str(excinfo.value)
        assert "Montant" in message
        assert "Canal" in message
        assert len(excinfo.value.errors) == 2

    def test_base_schema_enforced(self):
        registry = self.make_registry()
        # Name manquant, Uuid mal formé → violations du socle commun.
        with pytest.raises(EventSchemaError, match="Name|Uuid"):
            registry.validate(
                "schema_DemandeSoumise", {"Uuid": "pas-un-uuid", "Montant": 1}
            )

    def test_event_document_round_trip(self):
        from datetime import datetime, timezone

        from urban_workflow import IncomingEvent
        from urban_workflow.engine.serializer import event_to_document

        registry = self.make_registry()
        event = IncomingEvent(
            name="DemandeSoumise",
            external_id="DA-1",
            event_date=datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc),
            extended_datas={"Montant": 120, "Canal": "web"},
        )
        document = event_to_document(event)
        assert document["Name"] == "DemandeSoumise"
        assert document["Montant"] == 120
        assert document["EventDate"].startswith("2026-11-04T10:00")
        registry.validate("schema_DemandeSoumise", document)


class TestDedupHash:
    def test_hash_depends_only_on_listed_keys(self):
        from urban_workflow.schemas import compute_dedup_hash

        keys = ["ExternalId", "Montant"]
        a = compute_dedup_hash(keys, {"ExternalId": "DA-1", "Montant": 120, "Autre": 1})
        b = compute_dedup_hash(keys, {"ExternalId": "DA-1", "Montant": 120, "Autre": 2})
        c = compute_dedup_hash(keys, {"ExternalId": "DA-1", "Montant": 121})
        assert a == b
        assert a != c
        assert len(a) == 64  # sha256 hex

    def test_missing_key_counts_as_empty(self):
        from urban_workflow.schemas import compute_dedup_hash

        assert compute_dedup_hash(["X"], {}) == compute_dedup_hash(["X"], {"X": ""})


# ----------------------------------------------------------------------
# Moteur : anti-doublon A (UNIQUE) + B (DedupKey), validation à l'entrée
# ----------------------------------------------------------------------


def make_engine(script: str, schemas=None):
    from uuid import uuid4  # noqa: F401

    from urban_workflow import (
        MemoryStorage,
        Workflow,
        WorkflowEngine,
        WorkflowFactory,
        WorkflowProcessor,
        WorkflowsConfig,
    )
    from urban_workflow.outputs import default_memory_output

    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(
        parse_config(script, rules=FunctionRegistry("rule"), schemas=schemas)
    )
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage


UNIQUE_SCRIPT = """
NAME Demo
DEFINE EVENT DemandeSoumise 'dépôt' UNIQUE (ExternalId, Montant);
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert'
    ON EVENT DemandeSoumise
        SWITCH Ouvert
;
"""


class TestEngineDedup:
    def _payload(self, **extra):
        from uuid import uuid4

        return {"Name": "DemandeSoumise", "Uuid": str(uuid4()),
                "ExternalId": "DA-1", **extra}

    def test_unique_properties_block_functional_duplicates(self):
        from urban_workflow import Workflow

        engine, storage = make_engine(UNIQUE_SCRIPT)

        engine.evaluate_event(self._payload(Montant=120))
        engine.evaluate_event(self._payload(Montant=120))  # doublon (uuid ≠)
        workflows = storage.get_by(Workflow, "DA-1", "external_id")
        assert len(workflows) == 1
        assert len(workflows[0].events) == 1
        assert len(workflows[0].events[0].dedup_hash) == 64

        engine.evaluate_event(self._payload(Montant=121))  # valeur différente
        workflows = storage.get_by(Workflow, "DA-1", "external_id")
        assert len(workflows[0].events) == 2

    def test_emitter_dedup_key_wins_over_unique(self):
        from urban_workflow import Workflow

        engine, storage = make_engine(UNIQUE_SCRIPT)

        # Montants différents (UNIQUE dirait « distincts ») mais même
        # DedupKey émetteur → le second est un doublon.
        engine.evaluate_event(self._payload(Montant=120, DedupKey="cmd-1"))
        engine.evaluate_event(self._payload(Montant=999, DedupKey="cmd-1"))
        workflows = storage.get_by(Workflow, "DA-1", "external_id")
        assert len(workflows[0].events) == 1

        engine.evaluate_event(self._payload(Montant=999, DedupKey="cmd-2"))
        workflows = storage.get_by(Workflow, "DA-1", "external_id")
        assert len(workflows[0].events) == 2

    def test_dedup_key_alone_without_unique(self):
        from urban_workflow import Workflow

        script = UNIQUE_SCRIPT.replace(" UNIQUE (ExternalId, Montant)", "")
        engine, storage = make_engine(script)

        engine.evaluate_event(self._payload(Montant=1, DedupKey="x"))
        engine.evaluate_event(self._payload(Montant=2, DedupKey="x"))
        engine.evaluate_event(self._payload(Montant=3))  # sans clé : passe
        workflows = storage.get_by(Workflow, "DA-1", "external_id")
        assert len(workflows[0].events) == 2

    def test_dedup_key_is_a_typed_base_property(self):
        from urban_workflow import parse_incoming_event

        event = parse_incoming_event(self._payload(Montant=1, DedupKey="cmd-7"))
        assert event.dedup_key == "cmd-7"
        assert "DedupKey" not in event.extended_datas


class TestEngineSchemaValidation:
    @pytest.fixture(autouse=True)
    def _requires(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")

    def test_invalid_payload_raises_at_evaluation(self):
        from urban_workflow.schemas import SchemaRegistry

        registry = SchemaRegistry().add_yaml(
            "schema_DemandeSoumise",
            "type: object\nproperties: {Montant: {type: number}}\nrequired: [Montant]",
        )
        script = UNIQUE_SCRIPT.replace(
            "'dépôt' UNIQUE", "'dépôt' AS @schema_DemandeSoumise UNIQUE"
        )
        engine, storage = make_engine(script, schemas=registry)

        with pytest.raises(EventSchemaError, match="Montant"):
            engine.evaluate_event(self._payload(Montant="beaucoup"))

        engine.evaluate_event(self._payload(Montant=12))  # conforme
        from urban_workflow import Workflow

        assert len(storage.get_by(Workflow, "DA-1", "external_id")) == 1

    def _payload(self, **extra):
        from uuid import uuid4

        return {"Name": "DemandeSoumise", "Uuid": str(uuid4()),
                "ExternalId": "DA-1", **extra}


class TestIntegrationDate:
    """IntegrationDate : date d'insertion dans le système, posée par le
    moteur (jamais par l'émetteur), portée par l'historique."""

    def _payload(self, **extra):
        from uuid import uuid4

        return {"Name": "DemandeSoumise", "Uuid": str(uuid4()),
                "ExternalId": "DA-1", **extra}

    def test_engine_stamps_integration_date_with_the_clock(self):
        from datetime import datetime, timezone

        from urban_workflow import Workflow, WorkflowClock

        engine, storage = make_engine(UNIQUE_SCRIPT)
        instant = datetime(2026, 11, 5, 9, 30, tzinfo=timezone.utc)
        with WorkflowClock.frozen(instant):
            engine.evaluate_event(self._payload(Montant=1))

        event = storage.get_by(Workflow, "DA-1", "external_id")[0].events[0]
        assert event.integration_date == instant

    def test_emitter_value_is_ignored(self):
        from datetime import datetime, timezone

        from urban_workflow import Workflow, WorkflowClock, parse_incoming_event

        parsed = parse_incoming_event(
            self._payload(IntegrationDate="2000-01-01T00:00:00+00:00")
        )
        assert parsed.integration_date is None
        assert "IntegrationDate" not in parsed.extended_datas

        engine, storage = make_engine(UNIQUE_SCRIPT)
        instant = datetime(2026, 11, 5, 9, 30, tzinfo=timezone.utc)
        with WorkflowClock.frozen(instant):
            engine.evaluate_event(
                self._payload(Montant=1, IntegrationDate="2000-01-01T00:00:00+00:00")
            )
        event = storage.get_by(Workflow, "DA-1", "external_id")[0].events[0]
        assert event.integration_date == instant

    def test_base_schema_declares_it_read_only(self):
        from urban_workflow.schemas import BASE_EVENT_SCHEMA

        prop = BASE_EVENT_SCHEMA["properties"]["IntegrationDate"]
        assert prop["format"] == "date-time"
        assert prop["readOnly"] is True

    def test_document_carries_integration_date(self):
        from datetime import datetime, timezone

        from urban_workflow import IncomingEvent
        from urban_workflow.engine.serializer import event_to_document

        instant = datetime(2026, 11, 5, 9, 30, tzinfo=timezone.utc)
        document = event_to_document(
            IncomingEvent(name="X", integration_date=instant)
        )
        assert document["IntegrationDate"] == instant.isoformat()
