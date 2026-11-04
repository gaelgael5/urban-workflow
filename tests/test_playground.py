"""API du playground web (extra ``[playground]``) — skip sans fastapi."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from playground.app import app

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
