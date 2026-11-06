"""Règles écrites dans le DSL : ``DEFINE RULE R (…) 'l' AS <expression>;``.

Décisions de cadrage (2026-11-05) :
- le corps s'écrit dans le ``DEFINE RULE`` (nommé, réutilisable, typé) et
  s'appelle comme une règle de code : ``WHEN R(seuil = '1000')`` ;
- première version complète : comparaisons et logique, ``IN``, calcul,
  fonctions usuelles (``NOW``, écarts de dates, ``LENGTH``, ``CONTAINS``) ;
- coexistence avec les règles Python ; corps ET fonction pour un même nom
  = erreur au chargement.
"""

from __future__ import annotations

from datetime import datetime, timezone
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
from urban_workflow.dsl.surface import extract_surface, render_script
from urban_workflow.exceptions import (
    DslSyntaxError,
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
)
from urban_workflow.outputs import default_memory_output

TEMPLATE = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE RULE R ({decl}) 'règle' AS {body};
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN R({args}) SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""


def _engine(script: str, rules: FunctionRegistry | None = None, schemas=None):
    config = parse_config(script, rules=rules or FunctionRegistry("rule"), schemas=schemas)
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage


def _passes(body: str, payload: dict | None = None, decl: str = "", args: str = "") -> bool:
    """La règle passe-t-elle ? (= le workflow est-il créé)"""
    engine, storage = _engine(TEMPLATE.format(decl=decl, body=body, args=args))
    engine.evaluate_event(
        {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K", **(payload or {})}
    )
    return bool(storage.get_all(Workflow))


class TestComparisonsAndLogic:
    def test_parameter_against_event_path(self):
        body = "@IncomingEvent.Montant > seuil"
        assert _passes(body, {"Montant": 1500}, "DECIMAL seuil", "seuil = '1000'")
        assert not _passes(body, {"Montant": 500}, "DECIMAL seuil", "seuil = '1000'")

    @pytest.mark.parametrize(
        "body, expected",
        [
            ("@IncomingEvent.Canal = 'web'", True),
            ("@IncomingEvent.Canal != 'web'", False),
            ("@IncomingEvent.Canal <> 'mobile'", True),
            ("@IncomingEvent.Montant >= 100", True),
            ("@IncomingEvent.Montant <= 99.5", False),
            ("@IncomingEvent.Montant < 100.5 AND @IncomingEvent.Canal = 'web'", True),
            ("@IncomingEvent.Montant > 1000 OR @IncomingEvent.Canal = 'web'", True),
            ("NOT @IncomingEvent.Canal = 'mobile'", True),  # NOT (a = b)
            ("TRUE", True),
            ("FALSE OR (TRUE AND NOT FALSE)", True),
        ],
    )
    def test_operators(self, body, expected):
        assert _passes(body, {"Montant": 100, "Canal": "web"}) is expected

    def test_in_and_not_in(self):
        assert _passes("@IncomingEvent.Canal IN ('web', 'mobile')", {"Canal": "web"})
        assert not _passes("@IncomingEvent.Canal IN ('guichet')", {"Canal": "web"})
        assert _passes("@IncomingEvent.Canal NOT IN ('guichet')", {"Canal": "web"})

    def test_null_tests(self):
        assert _passes("@IncomingEvent.Absent IS NULL")
        assert not _passes("@IncomingEvent.Canal IS NULL", {"Canal": "web"})
        assert _passes("@IncomingEvent.Canal IS NOT NULL", {"Canal": "web"})


class TestArithmetic:
    def test_precedence(self):
        assert _passes("2 + 3 * 4 = 14")
        assert _passes("(2 + 3) * 4 = 20")
        assert _passes("-@IncomingEvent.Montant = -5", {"Montant": 5})

    def test_computed_threshold(self):
        body = "@IncomingEvent.Montant * 1.2 > seuil"
        assert _passes(body, {"Montant": 900}, "DECIMAL seuil", "seuil = '1000'")

    def test_null_and_impossible_operations_never_raise(self):
        # Absent, division par zéro, types incompatibles : NULL, donc la
        # comparaison est fausse — l'événement est traité sans exception.
        assert not _passes("@IncomingEvent.Absent + 1 > 0")
        assert not _passes("@IncomingEvent.Montant / 0 > 0", {"Montant": 5})
        assert not _passes("@IncomingEvent.Canal > 3", {"Canal": "web"})
        assert _passes("@IncomingEvent.Montant / 0 IS NULL", {"Montant": 5})


class TestFunctions:
    def test_length_and_contains(self):
        payload = {"Lignes": [1, 2, 3], "Libelle": "commande urgente"}
        assert _passes("LENGTH(@IncomingEvent.Lignes) = 3", payload)
        assert _passes("CONTAINS(@IncomingEvent.Libelle, 'urgent')", payload)
        assert _passes("CONTAINS(@IncomingEvent.Lignes, 2)", payload)
        assert _passes("length(@IncomingEvent.Libelle) > 5", payload)  # casse libre

    def test_dates_against_now(self):
        now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        payload = {"Echeance": "2026-11-01T12:00:00+00:00"}
        with WorkflowClock.frozen(now):
            assert _passes("DAYS_BETWEEN(@IncomingEvent.Echeance, NOW()) = 4", payload)
            assert _passes("HOURS_BETWEEN(@IncomingEvent.Echeance, NOW()) = 96", payload)
            assert _passes("MINUTES_BETWEEN(@IncomingEvent.Echeance, NOW()) > 60", payload)
            assert _passes("@IncomingEvent.Echeance < NOW()", payload)
            assert not _passes("DAYS_BETWEEN(@IncomingEvent.Absent, NOW()) > 0")

    def test_state_age_in_a_state_block(self):
        script = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE EVENT Relance 'r';
DEFINE RULE Ancien (INTEGER jours) 'état ancien'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= jours;
INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert'
    ON EVENT Relance WHEN Ancien(jours = '3') SWITCH Relance
;
DEFINE STATE Relance 'relancé' ;
"""
        engine, storage = _engine(script)
        with WorkflowClock.frozen(datetime(2026, 11, 1, tzinfo=timezone.utc)):
            engine.evaluate_event({"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K"})
        with WorkflowClock.frozen(datetime(2026, 11, 2, tzinfo=timezone.utc)):
            engine.evaluate_event({"Name": "Relance", "Uuid": str(uuid4()), "ExternalId": "K"})
        assert storage.get_all(Workflow)[0].current_state == "Ouvert"
        with WorkflowClock.frozen(datetime(2026, 11, 5, tzinfo=timezone.utc)):
            engine.evaluate_event({"Name": "Relance", "Uuid": str(uuid4()), "ExternalId": "K"})
        assert storage.get_all(Workflow)[0].current_state == "Relance"


class TestIdentifiers:
    def test_constant_declared_after_the_rule(self):
        script = TEMPLATE.format(decl="", body="@IncomingEvent.Montant > Plafond", args="")
        script = script.replace("INITIALIZE", "DEFINE CONST Plafond 1000 'plafond';\nINITIALIZE")
        engine, storage = _engine(script)
        engine.evaluate_event(
            {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K", "Montant": 2000}
        )
        assert storage.get_all(Workflow)

    def test_unknown_identifier_is_positioned(self):
        with pytest.raises(InvalidArgumentNameError, match=r"x\.wf:\d+:\d+.*seuill"):
            parse_config(
                TEMPLATE.format(decl="DECIMAL seuil", body="@IncomingEvent.M > seuill",
                                args="seuil = '1'"),
                filename="x.wf",
            )

    def test_unknown_function_and_arity(self):
        with pytest.raises(InvalidMethodReferenceError, match="TODAY"):
            parse_config(TEMPLATE.format(decl="", body="TODAY() = 1", args=""))
        with pytest.raises(InvalidArgumentValueError, match="LENGTH expects 1"):
            parse_config(TEMPLATE.format(decl="", body="LENGTH() = 1", args=""))

    def test_syntax_error(self):
        with pytest.raises(DslSyntaxError):
            parse_config(TEMPLATE.format(decl="", body="1 >", args="")).build()


class TestCallSites:
    def test_missing_argument(self):
        with pytest.raises(MissingArgumentNameError, match="seuil"):
            parse_config(TEMPLATE.format(decl="DECIMAL seuil", body="seuil > 1", args=""))

    def test_unknown_argument(self):
        with pytest.raises(InvalidArgumentNameError, match="autre"):
            parse_config(TEMPLATE.format(decl="", body="TRUE", args="autre = '1'"))

    def test_state_path_called_from_initialize_is_rejected_with_the_call(self):
        with pytest.raises(InvalidArgumentValueError, match=r"@state.*called at x\.wf:\d+"):
            parse_config(
                TEMPLATE.format(decl="", body="@state.Name = 'Ouvert'", args=""),
                filename="x.wf",
            )

    def test_event_path_checked_against_the_calling_event_schema(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        from urban_workflow.schemas import SchemaRegistry

        schemas = SchemaRegistry().add_yaml(
            "schema_Ouverture", "type: object\nproperties:\n  Montant: {type: number}\n"
        )
        script = TEMPLATE.format(decl="", body="@IncomingEvent.Montnt > 1", args="").replace(
            "DEFINE EVENT Ouverture 'o';", "DEFINE EVENT Ouverture 'o' AS @schema_Ouverture;"
        )
        with pytest.raises(InvalidArgumentValueError, match="Montnt.*called at"):
            parse_config(script, schemas=schemas)

    def test_call_is_logged_like_a_code_rule(self):
        engine, storage = _engine(
            TEMPLATE.format(decl="DECIMAL seuil", body="seuil > 1", args="seuil = '2'")
        )
        contexts = engine.evaluate_event(
            {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K"}
        )
        assert "R(seuil=2.0) -> True" in contexts[0].functional_log


class TestCoexistence:
    def test_body_and_code_for_the_same_name_is_rejected(self):
        rules = FunctionRegistry("rule").add("R", lambda ctx: True)
        with pytest.raises(DuplicatedArgumentNameError, match="body"):
            parse_config(TEMPLATE.format(decl="", body="TRUE", args=""), rules=rules)

    def test_code_rules_still_work_next_to_body_rules(self):
        script = TEMPLATE.format(decl="", body="TRUE", args="").replace(
            "WHEN R()", "WHEN R() AND Code()"
        ).replace("DEFINE RULE R", "DEFINE RULE Code () 'code';\nDEFINE RULE R")
        rules = FunctionRegistry("rule").add("Code", lambda ctx: True)
        engine, storage = _engine(script, rules)
        engine.evaluate_event({"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K"})
        assert storage.get_all(Workflow)


class TestSurface:
    def test_body_survives_the_diagram_round_trip(self):
        script = TEMPLATE.format(
            decl="DECIMAL seuil", body="@IncomingEvent.Montant > seuil AND TRUE",
            args="seuil = '1'",
        )
        model = extract_surface(script)
        assert model.rules[0].body == "@IncomingEvent.Montant > seuil AND TRUE"
        rendered = render_script(model)
        assert "AS @IncomingEvent.Montant > seuil AND TRUE;" in rendered
        assert render_script(extract_surface(rendered)) == rendered
        parse_config(rendered)


MULTILINE = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE RULE Eligible (DECIMAL seuil) 'règle sur plusieurs lignes'
    AS -- le montant compte double pour un client fidèle
       @IncomingEvent.Montant * 2 > seuil
       /* canaux acceptés */
       AND @IncomingEvent.Canal IN ('web',
                                    'mobile');
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN Eligible(seuil = '100') SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""


class TestMultiline:
    """Le corps est une expression libre : sauts de ligne et commentaires
    sont permis partout entre ``AS`` et le ``;``."""

    def test_multiline_body_with_comments_is_evaluated(self):
        for payload, expected in [
            ({"Montant": 60, "Canal": "mobile"}, True),
            ({"Montant": 40, "Canal": "mobile"}, False),
            ({"Montant": 60, "Canal": "guichet"}, False),
        ]:
            engine, storage = _engine(MULTILINE)
            engine.evaluate_event(
                {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K", **payload}
            )
            assert bool(storage.get_all(Workflow)) is expected, payload

    def test_error_points_to_the_line_inside_the_body(self):
        script = MULTILINE.replace("AND @IncomingEvent.Canal", "AND seuill")
        with pytest.raises(InvalidArgumentNameError, match=r"x\.wf:8:\d+.*seuill"):
            parse_config(script, filename="x.wf")

    def test_multiline_body_is_a_fixed_point_of_the_round_trip(self):
        rendered = render_script(extract_surface(MULTILINE))
        assert render_script(extract_surface(rendered)) == rendered
        assert "       AND @IncomingEvent.Canal IN ('web'," in rendered
        parse_config(rendered)
