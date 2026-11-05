"""API du playground web (distribution urban-workflow-playground) — skip sans fastapi."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from urban_workflow_playground.app import app

client = TestClient(app)

RULES = [
    {"name": "EstComplet", "params": [{"name": "champs", "type": "TEXT"}], "result": True},
    {
        "name": "MontantInferieur",
        "params": [{"name": "seuil", "type": "DECIMAL"}],
        "result": True,
    },
]

SCRIPT = """
NAME Demo VERSION 1
DEFINE EVENT Ouverture 'ouverture';
DEFINE RULE  EstComplet (TEXT champs) 'complet';
DEFINE ACTION Notifier (TEXT cible) 'notification';
DEFINE CONST seuil 500 'seuil';
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN EstComplet(champs = 'Montant') SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert'
    ON ENTER STATE
        EXECUTE Notifier(cible = @Workflow.ExternalId)
;
"""


class TestAnalyze:
    def test_valid_script(self):
        response = client.post(
            "/api/analyze", json={"script": SCRIPT, "rules": RULES}
        )
        data = response.json()
        assert data["ok"] is True
        assert data["errors"] == []
        assert data["symbols"]["events"] == ["$_result", "Ouverture"]
        assert data["symbols"]["states"] == ["Ouvert"]
        assert data["symbols"]["rules"][0]["name"] == "EstComplet"
        assert data["symbols"]["actions"][0]["params"] == [
            {"name": "cible", "type": "TEXT"}
        ]
        assert data["summary"]["name"] == "Demo"
        assert data["summary"]["initializers"][0]["event"] == "Ouverture"

    def test_syntax_error_is_positioned(self):
        response = client.post(
            "/api/analyze",
            json={"script": "NAME Demo\nDEFINE EVENT X 'x'", "rules": []},
        )
        data = response.json()
        assert data["ok"] is False
        assert data["errors"][0]["line"] >= 1

    def test_semantic_error_is_positioned_and_symbols_survive(self):
        script = SCRIPT.replace("EXECUTE Notifier(cible", "EXECUTE Inconnue(cible")
        response = client.post(
            "/api/analyze", json={"script": script, "rules": RULES}
        )
        data = response.json()
        assert data["ok"] is False
        error = data["errors"][0]
        assert "Inconnue" in error["message"]
        assert error["line"] > 1
        # Le repli regex garde les symboles pour l'intellisense.
        assert "Ouverture" in data["symbols"]["events"]
        assert "Ouvert" in data["symbols"]["states"]

    def test_unregistered_rule_reported(self):
        response = client.post(
            "/api/analyze", json={"script": SCRIPT, "rules": []}
        )
        data = response.json()
        assert data["ok"] is False
        assert "EstComplet" in data["errors"][0]["message"]


class TestSimulate:
    def test_simulation_runs_events(self):
        response = client.post(
            "/api/simulate",
            json={
                "script": SCRIPT,
                "rules": RULES,
                "events": [
                    {
                        "Name": "Ouverture",
                        "Uuid": "11111111-1111-4111-8111-111111111111",
                        "ExternalId": "D-1",
                        "Montant": 120,
                    }
                ],
            },
        )
        data = response.json()
        assert data["ok"] is True

        step = data["steps"][0]
        assert step["impacted"][0]["to_state"] == "Ouvert"
        action = step["impacted"][0]["actions"][0]
        assert action["name"] == "Notifier"
        assert action["message"]["Body"]["Arguments"] == {"cible": "D-1"}
        assert step["impacted"][0]["log"]  # journal fonctionnel rempli

        assert data["workflows"][0]["state"] == "Ouvert"

    def test_simulation_with_false_rule(self):
        rules = [dict(RULES[0], result=False), RULES[1]]
        response = client.post(
            "/api/simulate",
            json={
                "script": SCRIPT,
                "rules": rules,
                "events": [
                    {
                        "Name": "Ouverture",
                        "Uuid": "21111111-1111-4111-8111-111111111111",
                        "ExternalId": "D-2",
                    }
                ],
            },
        )
        data = response.json()
        assert data["ok"] is True
        assert data["steps"][0]["impacted"] == []
        assert data["workflows"] == []

    def test_broken_script_reports_error(self):
        response = client.post(
            "/api/simulate",
            json={"script": "NAME x DEFINE EVENT e 'e'", "rules": [], "events": []},
        )
        data = response.json()
        assert data["ok"] is False
        assert data["error"]


class TestStatic:
    def test_index_served(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "playground DSL" in response.text

    def test_vendor_codemirror_served(self):
        response = client.get("/static/vendor/codemirror.js")
        assert response.status_code == 200

    def test_diagram_assets_served(self):
        assert client.get("/static/vendor/x6.min.js").status_code == 200
        assert client.get("/static/diagram.js").status_code == 200


SCHEMA_SCRIPT = """
NAME Demo VERSION 1
DEFINE EVENT Ouverture 'ouverture'
    AS @schema_Ouverture UNIQUE (ExternalId, Montant);
INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""

SCHEMA_YAML = (
    "title: Ouverture\n"
    "type: object\n"
    "properties:\n"
    "  Montant: {type: number, minimum: 0}\n"
    "required: [Montant]\n"
)


class TestSchemasInPlayground:
    @pytest.fixture(autouse=True)
    def _requires(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")

    def test_analyze_resolves_schema_and_exposes_symbols(self):
        data = client.post(
            "/api/analyze",
            json={
                "script": SCHEMA_SCRIPT,
                "rules": [],
                "schemas": [{"name": "schema_Ouverture", "yaml": SCHEMA_YAML}],
            },
        ).json()
        assert data["ok"] is True
        assert data["symbols"]["schemas"] == ["schema_Ouverture"]
        assert data["symbols"]["event_details"] == [
            {"name": "Ouverture", "schema_ref": "schema_Ouverture",
             "unique": ["ExternalId", "Montant"]}
        ]
        assert "Montant" in data["symbols"]["payload_properties"]
        assert "DedupKey" in data["symbols"]["payload_properties"]
        assert data["summary"]["events"][0]["schema_ref"] == "schema_Ouverture"

    def test_unknown_schema_reference_is_positioned(self):
        data = client.post(
            "/api/analyze",
            json={"script": SCHEMA_SCRIPT, "rules": [],
                  "schemas": [{"name": "autre", "yaml": "type: object"}]},
        ).json()
        assert data["ok"] is False
        assert "schema_Ouverture" in data["errors"][0]["message"]
        assert data["errors"][0]["line"] > 1

    def test_invalid_yaml_reported_globally(self):
        data = client.post(
            "/api/analyze",
            json={"script": SCHEMA_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouverture", "yaml": "- [pas: un objet"}]},
        ).json()
        assert data["ok"] is False
        assert "schema_Ouverture" in data["errors"][0]["message"]

    def test_simulate_validates_and_dedups(self):
        payloads = [
            # payload invalide : Montant chaîne → EventSchemaError sur l'étape
            {"Name": "Ouverture", "Uuid": "11111111-1111-4111-8111-111111111111",
             "ExternalId": "D-1", "Montant": "beaucoup"},
            # valide
            {"Name": "Ouverture", "Uuid": "21111111-1111-4111-8111-111111111111",
             "ExternalId": "D-1", "Montant": 10},
            # doublon fonctionnel (UNIQUE ExternalId+Montant, uuid différent)
            {"Name": "Ouverture", "Uuid": "31111111-1111-4111-8111-111111111111",
             "ExternalId": "D-1", "Montant": 10},
        ]
        data = client.post(
            "/api/simulate",
            json={"script": SCHEMA_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouverture", "yaml": SCHEMA_YAML}],
                  "events": payloads},
        ).json()
        assert data["ok"] is True
        assert "EventSchemaError" in data["steps"][0]["error"]
        assert data["steps"][1]["impacted"][0]["to_state"] == "Ouvert"
        assert data["steps"][2]["impacted"] == []  # doublon ignoré
        assert len(data["workflows"]) == 1
        assert len(data["workflows"][0]["events"]) == 1

class TestDiagram:
    def test_script_to_model(self):
        data = client.post("/api/diagram", json={"script": SCRIPT}).json()
        assert data["ok"] is True
        model = data["model"]
        assert model["name"] == "Demo"
        assert [s["name"] for s in model["states"]] == ["Ouvert"]
        init = model["initializers"][0]
        assert (init["event"], init["switch"]) == ("Ouverture", "Ouvert")
        assert init["when"] == "EstComplet(champs = 'Montant')"
        enter = model["states"][0]["actions"][0]
        assert enter["trigger"] == "ENTER"
        assert enter["execute"].startswith("EXECUTE Notifier(")

    def test_schema_fields_survive(self):
        data = client.post("/api/diagram", json={"script": SCHEMA_SCRIPT}).json()
        assert data["ok"] is True
        event = data["model"]["events"][0]
        assert event["schema_ref"] == "schema_Ouverture"
        assert event["unique"] == ["ExternalId", "Montant"]

    def test_syntax_error_positioned(self):
        data = client.post(
            "/api/diagram", json={"script": "NAME Demo\nDEFINE EVENT X 'x'"}
        ).json()
        assert data["ok"] is False
        assert data["model"] is None
        assert data["errors"][0]["line"] >= 1

    def test_generate_roundtrip(self):
        model = client.post("/api/diagram", json={"script": SCRIPT}).json()["model"]
        data = client.post(
            "/api/generate", json={"model": model, "rules": RULES}
        ).json()
        assert data["ok"] is True, data["errors"]
        assert "INITIALIZE WORKFLOW" in data["script"]
        assert data["summary"]["name"] == "Demo"
        # Le script généré se réimporte à l'identique (point fixe via HTTP).
        again = client.post(
            "/api/diagram", json={"script": data["script"]}
        ).json()
        assert again["ok"] is True
        regenerated = client.post(
            "/api/generate", json={"model": again["model"], "rules": RULES}
        ).json()
        assert regenerated["script"] == data["script"]

    def test_generate_reports_validation_errors(self):
        model = client.post("/api/diagram", json={"script": SCRIPT}).json()["model"]
        model["initializers"][0]["switch"] = "EtatInconnu"
        data = client.post(
            "/api/generate", json={"model": model, "rules": RULES}
        ).json()
        assert data["ok"] is False
        assert any("EtatInconnu" in e["message"] for e in data["errors"])
        assert "SWITCH EtatInconnu" in data["script"]


class TestHealthz:
    """Sonde de santé visée par dev-deploy.sh et le HEALTHCHECK de l'image."""

    def test_healthz_reports_ok(self):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestFavicon:
    """Le navigateur réclame /favicon.ico : sans réponse, 404 dans la console."""

    def test_favicon_ico_is_served_as_svg(self):
        response = client.get("/favicon.ico")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/svg+xml")
        assert response.text.lstrip().startswith("<svg")

    def test_index_declares_the_icon(self):
        assert 'rel="icon"' in client.get("/").text

    def test_index_offers_the_side_pane_collapse_toggle(self):
        # Bouton de repli du panneau de droite (le comportement lui-même est
        # éprouvé dans un vrai navigateur sur la machine de test).
        assert 'id="side-collapse"' in client.get("/").text
