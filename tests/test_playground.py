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
                        # Ignorée : c'est le moteur qui date l'intégration.
                        "IntegrationDate": "2000-01-01T00:00:00+00:00",
                    }
                ],
            },
        )
        data = response.json()
        assert data["ok"] is True
        integrated = data["workflows"][0]["events"][0]["integration_date"]
        assert integrated and not integrated.startswith("2000")
        (state,) = data["workflows"][0]["states"]
        assert state["name"] == "Ouvert"
        assert state["event_id"] == "11111111-1111-4111-8111-111111111111"

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
            {"name": "Ouverture", "label": "ouverture",
             "schema_ref": "schema_Ouverture", "unique": ["ExternalId", "Montant"],
             "declared": True}
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


class TestAssetVersioning:
    """Sans version dans l'URL, le navigateur garde l'ancien app.js/style.css
    après un déploiement : page neuve + scripts périmés (vu sur le repli du
    panneau de droite)."""

    def test_static_assets_carry_a_content_version(self):
        import re

        html = client.get("/").text
        refs = re.findall(r'(?:href|src)="(/static/[^"]+)"', html)
        assert refs, "la page doit référencer ses fichiers statiques"
        for ref in refs:
            assert re.search(r"\?v=[0-9a-f]{12}$", ref), ref

    def test_versioned_asset_is_still_served(self):
        import re

        html = client.get("/").text
        ref = re.search(r'src="(/static/app\.js\?v=[0-9a-f]+)"', html).group(1)
        assert client.get(ref).status_code == 200

    def test_index_is_revalidated_on_each_load(self):
        assert client.get("/").headers["cache-control"] == "no-cache"


class TestEventsView:
    """Vue « Événements » : socle exposé, tous les événements listés,
    champs du socle protégés contre la redéfinition."""

    def test_base_event_schema_is_served_from_the_core(self):
        from urban_workflow.schemas import BASE_EVENT_SCHEMA

        response = client.get("/api/base-event-schema")
        assert response.status_code == 200
        assert response.json() == BASE_EVENT_SCHEMA

    def test_event_details_list_every_declared_event(self):
        data = client.post(
            "/api/analyze", json={"script": SCRIPT, "rules": RULES}
        ).json()
        assert data["symbols"]["event_details"] == [
            {"name": "Ouverture", "label": "ouverture", "schema_ref": "",
             "unique": [], "declared": True}
        ]

    def test_used_but_undeclared_event_is_flagged(self):
        script = SCRIPT.replace(
            "EXECUTE Notifier(cible = @Workflow.ExternalId)\n;",
            "EXECUTE Notifier(cible = @Workflow.ExternalId)\n"
            "    ON EVENT Cloture SWITCH Ferme\n;\n"
            "DEFINE STATE Ferme 'fermé' ;",
        )
        assert "Cloture" in script
        data = client.post(
            "/api/analyze", json={"script": script, "rules": RULES}
        ).json()
        assert data["ok"] is True, data["errors"]
        details = {d["name"]: d["declared"] for d in data["symbols"]["event_details"]}
        assert details == {"Ouverture": True, "Cloture": False}

    def test_business_schema_cannot_redefine_a_base_field(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        yaml_text = "type: object\nproperties:\n  Uuid: {type: integer}\n  Montant: {type: number}\n"
        data = client.post(
            "/api/analyze",
            json={"script": SCHEMA_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouverture", "yaml": yaml_text}]},
        ).json()
        assert data["ok"] is False
        message = data["errors"][0]["message"]
        assert "schema_Ouverture" in message and "Uuid" in message and "socle" in message


class TestEventPathsInPlayground:
    """Intellisense après @IncomingEvent. : chemins de chaque événement (socle + schéma)."""

    def test_event_properties_flatten_schema_paths(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        yaml_text = (
            "type: object\nproperties:\n"
            "  Montant: {type: number}\n"
            "  Client: {type: object, properties: {Pays: {type: string}}}\n"
            "  Lignes: {type: array, items: {type: object, properties: {Qte: {type: integer}}}}\n"
        )
        data = client.post(
            "/api/analyze",
            json={"script": SCHEMA_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouverture", "yaml": yaml_text}]},
        ).json()
        assert data["ok"] is True, data["errors"]
        listed = [p["path"] for p in data["symbols"]["event_properties"]["Ouverture"]]
        # Champs métier d'abord (les plus recherchés), socle ensuite.
        assert listed[0] == "Montant"
        assert listed.index("Lignes[0].Qte") < listed.index("Name")
        paths = {p["path"]: p["type"] for p in data["symbols"]["event_properties"]["Ouverture"]}
        assert paths["Montant"] == "number"
        assert paths["Client.Pays"] == "string"
        assert paths["Lignes[0].Qte"] == "integer"
        assert paths["Name"] == "string" and "IntegrationDate" in paths  # socle

    def test_event_without_schema_offers_the_base_only(self):
        data = client.post("/api/analyze", json={"script": SCRIPT, "rules": RULES}).json()
        paths = [p["path"] for p in data["symbols"]["event_properties"]["Ouverture"]]
        assert "Name" in paths and "IntegrationDate" in paths and "Montant" not in paths
        base = [p["path"] for p in data["symbols"]["base_paths"]]
        assert "IntegrationDate" in base and "Montant" not in base

    def test_rule_argument_accepts_an_event_path(self):
        script = SCRIPT.replace(
            "EstComplet(champs = 'Montant')", "EstComplet(champs = @IncomingEvent.Name)"
        )
        assert "@IncomingEvent.Name" in script
        data = client.post("/api/analyze", json={"script": script, "rules": RULES}).json()
        assert data["ok"] is True, data["errors"]

    def test_event_paths_survive_a_script_being_typed(self):
        # Pendant la frappe de « @IncomingEvent. » le script ne compile pas : la
        # complétion doit quand même connaître le schéma de l'événement.
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        script = SCHEMA_SCRIPT.replace(
            "ON EVENT Ouverture SWITCH Ouvert",
            "ON EVENT Ouverture WHEN EstComplet(champs = @IncomingEvent.) SWITCH Ouvert",
        )
        data = client.post(
            "/api/analyze",
            json={"script": script, "rules": RULES,
                  "schemas": [{"name": "schema_Ouverture", "yaml": SCHEMA_YAML}]},
        ).json()
        assert data["ok"] is False
        paths = [p["path"] for p in data["symbols"]["event_properties"]["Ouverture"]]
        assert "Montant" in paths



STATE_SCRIPT = """
NAME Demo VERSION 1
DEFINE EVENT Ouverture 'ouverture';
INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' AS @schema_Ouvert ;
"""

STATE_YAML = "type: object\nproperties:\n  Decision: {type: string}\n"


class TestStatesInPlayground:
    """Vue « États » : socle d'état servi, détails et chemins @state."""

    def test_base_state_schema_is_served_from_the_core(self):
        from urban_workflow.schemas import BASE_STATE_SCHEMA

        assert client.get("/api/base-state-schema").json() == BASE_STATE_SCHEMA

    def test_state_details_and_paths(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        data = client.post(
            "/api/analyze",
            json={"script": STATE_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouvert", "yaml": STATE_YAML}]},
        ).json()
        assert data["ok"] is True, data["errors"]
        assert data["symbols"]["state_details"] == [
            {"name": "Ouvert", "label": "ouvert", "schema_ref": "schema_Ouvert"}
        ]
        listed = [p["path"] for p in data["symbols"]["state_properties"]["Ouvert"]]
        assert listed[0] == "Decision"  # métier d'abord
        assert {"Name", "Uuid", "CreationDate", "EventId"} <= set(listed)
        base = [p["path"] for p in data["symbols"]["base_state_paths"]]
        assert "EventId" in base and "Decision" not in base

    def test_state_details_survive_a_script_being_typed(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        script = STATE_SCRIPT.replace("SWITCH Ouvert\n", "SWITCH Ouvert\nDEFINE ;\n", 1)
        data = client.post(
            "/api/analyze",
            json={"script": script, "rules": [],
                  "schemas": [{"name": "schema_Ouvert", "yaml": STATE_YAML}]},
        ).json()
        assert data["ok"] is False
        listed = [p["path"] for p in data["symbols"]["state_properties"]["Ouvert"]]
        assert "Decision" in listed

    def test_state_schema_cannot_redefine_a_base_state_field(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        yaml_text = "type: object\nproperties:\n  EventId: {type: integer}\n"
        data = client.post(
            "/api/analyze",
            json={"script": STATE_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouvert", "yaml": yaml_text}]},
        ).json()
        assert data["ok"] is False
        message = " ".join(e["message"] for e in data["errors"])
        assert "schema_Ouvert" in message and "EventId" in message and "socle" in message

    def test_a_state_schema_may_use_an_event_base_name(self):
        # « ExternalId » appartient au socle des ÉVÉNEMENTS, pas des états :
        # un schéma d'état peut l'employer.
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        yaml_text = "type: object\nproperties:\n  ExternalId: {type: string}\n"
        data = client.post(
            "/api/analyze",
            json={"script": STATE_SCRIPT, "rules": [],
                  "schemas": [{"name": "schema_Ouvert", "yaml": yaml_text}]},
        ).json()
        assert data["ok"] is True, data["errors"]


SCRIPT_REF = """
NAME Demo
DEFINE EVENT Ouverture 'ouverture';
DEFINE RULE MontantEleve (DECIMAL seuil) 'montant élevé' AS @montant_eleve;
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN MontantEleve(seuil = '1000') SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""
SCRIPTS = [{"name": "montant_eleve", "language": "expression",
            "source": "-- montant\n@IncomingEvent.Montant > seuil"}]


class TestScripts:
    """Règles qui référencent un script (``AS @nom``) : évaluées par le
    moteur avec les scripts de la vue Scripts, sans entrée dans le panneau
    Paramétrage."""

    def test_analyze_without_panel_entry(self):
        data = client.post(
            "/api/analyze", json={"script": SCRIPT_REF, "scripts": SCRIPTS}
        ).json()
        assert data["ok"] is True, data["errors"]
        (rule,) = data["symbols"]["rules"]
        assert rule["script"] == "montant_eleve"
        assert data["symbols"]["scripts"] == [{"name": "montant_eleve", "language": "expression"}]

    def test_panel_entry_with_the_same_name_is_ignored(self):
        rules = [{"name": "MontantEleve", "params": [{"name": "seuil", "type": "DECIMAL"}],
                  "result": False}]
        data = client.post(
            "/api/analyze", json={"script": SCRIPT_REF, "rules": rules, "scripts": SCRIPTS}
        ).json()
        assert data["ok"] is True, data["errors"]

    def test_missing_script_is_flagged_on_the_reference(self):
        data = client.post("/api/analyze", json={"script": SCRIPT_REF}).json()
        assert data["ok"] is False
        (error,) = data["errors"]
        assert error["line"] == 4 and "montant_eleve" in error["message"]
        assert "script" not in error

    def test_script_syntax_error_is_positioned_in_the_script(self):
        broken = [{**SCRIPTS[0], "source": "@IncomingEvent.Montant >"}]
        data = client.post(
            "/api/analyze", json={"script": SCRIPT_REF, "scripts": broken}
        ).json()
        assert data["ok"] is False
        (error,) = data["errors"]  # pas de faux « script inconnu » en plus
        assert error["script"] == "montant_eleve" and error["line"] == 1

    def test_script_semantic_error_is_shown_in_the_script_and_at_the_call(self):
        wrong = [{**SCRIPTS[0], "source": "@IncomingEvent.Montant > seuill"}]
        data = client.post(
            "/api/analyze", json={"script": SCRIPT_REF, "scripts": wrong}
        ).json()
        in_script, at_call = data["errors"]
        assert in_script["script"] == "montant_eleve"
        assert (in_script["line"], in_script["column"]) == (1, 25)
        assert "seuill" in in_script["message"]
        # Contrôlé dès la déclaration : souligné sur la référence AS @.
        assert "script" not in at_call and at_call["line"] == 4
        assert at_call["message"].startswith("script @montant_eleve : ")

    def test_simulation_really_evaluates_the_script(self):
        def run(montant):
            data = client.post(
                "/api/simulate",
                json={"script": SCRIPT_REF, "scripts": SCRIPTS, "events": [
                    {"Name": "Ouverture", "ExternalId": "K", "Montant": montant}
                ]},
            ).json()
            assert data["ok"] is True, data
            return data["workflows"]

        assert run(1500)[0]["state"] == "Ouvert"
        assert run(500) == []

    def test_regex_fallback_keeps_references_while_typing(self):
        broken = SCRIPT_REF + "\nDEFINE STATE"  # script invalide pendant la frappe
        data = client.post("/api/analyze", json={"script": broken, "scripts": SCRIPTS}).json()
        assert data["ok"] is False
        (rule,) = data["symbols"]["rules"]
        assert rule["script"] == "montant_eleve"
