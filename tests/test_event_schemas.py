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
DEFINE EVENT DemandeSoumise 'une demande est déposée' AS @schema_DemandeSoumise;
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
        assert config.declared_events["Simple"].schema_ref == ""

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
            x-dedup: [ExternalId, Montant]
            """,
        )
        config = parse_config(SCRIPT, rules=FunctionRegistry("rule"), schemas=registry)
        declared = config.declared_events["DemandeSoumise"]
        assert declared.schema["title"] == "DemandeSoumise"
        assert declared.dedup_keys == ["ExternalId", "Montant"]


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
