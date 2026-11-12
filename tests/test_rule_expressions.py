"""Langage ``expression`` des scripts de règles.

Le workflow référence le script (``DEFINE RULE R (…) 'l' AS @r;``), le
ScriptRegistry porte l'expression (décision du 2026-11-07). Cadrage du
langage (2026-11-05) : comparaisons et logique, ``IN``, calcul, fonctions
usuelles (``NOW``, écarts de dates, ``LENGTH``, ``CONTAINS``) ; la règle
s'appelle comme une règle de code : ``WHEN R(seuil = '1000')``.
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
from urban_workflow.exceptions import (
    DslSyntaxError,
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
)
from urban_workflow.outputs import default_memory_output
from urban_workflow.scripts import ScriptRegistry

TEMPLATE = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE RULE R ({decl}) 'règle' AS @r;
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN R({args}) SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert' ;
"""


def _scripts(body: str, name: str = "r") -> ScriptRegistry:
    return ScriptRegistry().add_script(name, body, origin=f"{name}.expr")


def _load(body: str, decl: str = "", args: str = "", **kwargs):
    """Charge TEMPLATE avec ``body`` comme script ``@r``."""
    return parse_config(
        TEMPLATE.format(decl=decl, args=args), scripts=_scripts(body), **kwargs
    )


def _engine(script: str, rules: FunctionRegistry | None = None, schemas=None,
            scripts: ScriptRegistry | None = None):
    config = parse_config(script, rules=rules or FunctionRegistry("rule"), schemas=schemas,
                          scripts=scripts)
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage


def _passes(body: str, payload: dict | None = None, decl: str = "", args: str = "") -> bool:
    """La règle passe-t-elle ? (= le workflow est-il créé)"""
    engine, storage = _engine(TEMPLATE.format(decl=decl, args=args), scripts=_scripts(body))
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
DEFINE RULE Ancien (INTEGER jours) 'état ancien' AS @ancien;
INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert'
    ON EVENT Relance WHEN Ancien(jours = '3') SWITCH Relance
;
DEFINE STATE Relance 'relancé' ;
"""
        engine, storage = _engine(
            script, scripts=_scripts("DAYS_BETWEEN(@state.CreationDate, NOW()) >= jours", "ancien")
        )
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
        script = TEMPLATE.format(decl="", args="")
        script = script.replace("INITIALIZE", "DEFINE CONST Plafond 1000 'plafond';\nINITIALIZE")
        engine, storage = _engine(script, scripts=_scripts("@IncomingEvent.Montant > Plafond"))
        engine.evaluate_event(
            {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K", "Montant": 2000}
        )
        assert storage.get_all(Workflow)

    def test_unknown_identifier_is_positioned(self):
        # Positionnée DANS le script (r.expr:1:19), même sans appel.
        with pytest.raises(InvalidArgumentNameError, match=r"r\.expr:1:19: .*seuill"):
            _load("@IncomingEvent.M > seuill", "DECIMAL seuil", "seuil = '1'")

    def test_unknown_function_and_arity(self):
        with pytest.raises(InvalidMethodReferenceError, match="TODAY"):
            _load("TODAY() = 1")
        with pytest.raises(InvalidArgumentValueError, match="LENGTH expects 1"):
            _load("LENGTH() = 1")

    def test_syntax_error_is_raised_when_the_script_is_registered(self):
        with pytest.raises(DslSyntaxError, match=r"r\.expr:1:3"):
            _scripts("1 >")


class TestCallSites:
    def test_missing_argument(self):
        with pytest.raises(MissingArgumentNameError, match="seuil"):
            _load("seuil > 1", "DECIMAL seuil")

    def test_unknown_argument(self):
        with pytest.raises(InvalidArgumentNameError, match="autre"):
            _load("TRUE", args="autre = '1'")

    def test_state_path_called_from_initialize_is_rejected_with_the_call(self):
        with pytest.raises(
            InvalidArgumentValueError, match=r"^r\.expr:1:0: @state.*called at x\.wf:\d+"
        ):
            _load("@state.Name = 'Ouvert'", filename="x.wf")

    def test_event_path_checked_against_the_calling_event_schema(self):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        from urban_workflow.schemas import SchemaRegistry

        schemas = SchemaRegistry().add_yaml(
            "schema_Ouverture", "type: object\nproperties:\n  Montant: {type: number}\n"
        )
        script = TEMPLATE.format(decl="", args="").replace(
            "DEFINE EVENT Ouverture 'o';", "DEFINE EVENT Ouverture 'o' AS @schema_Ouverture;"
        )
        with pytest.raises(InvalidArgumentValueError, match="Montnt.*called at"):
            parse_config(script, schemas=schemas, scripts=_scripts("@IncomingEvent.Montnt > 1"))

    def test_call_is_logged_like_a_code_rule(self):
        engine, storage = _engine(
            TEMPLATE.format(decl="DECIMAL seuil", args="seuil = '2'"), scripts=_scripts("seuil > 1")
        )
        contexts = engine.evaluate_event(
            {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K"}
        )
        assert "R(seuil=2.0) -> True" in contexts[0].functional_log


class TestCoexistence:
    def test_script_and_code_for_the_same_name_is_rejected(self):
        rules = FunctionRegistry("rule").add("R", lambda ctx: True)
        with pytest.raises(DuplicatedArgumentNameError, match="script"):
            _load("TRUE", rules=rules)

    def test_code_rules_still_work_next_to_script_rules(self):
        script = TEMPLATE.format(decl="", args="").replace(
            "WHEN R()", "WHEN R() AND Code()"
        ).replace("DEFINE RULE R", "DEFINE RULE Code () 'code';\nDEFINE RULE R")
        rules = FunctionRegistry("rule").add("Code", lambda ctx: True)
        engine, storage = _engine(script, rules, scripts=_scripts("TRUE"))
        engine.evaluate_event({"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K"})
        assert storage.get_all(Workflow)


MULTILINE = """-- le montant compte double pour un client fidèle
@IncomingEvent.Montant * 2 > seuil
/* canaux acceptés */
AND @IncomingEvent.Canal IN ('web',
                             'mobile');
"""


class TestMultiline:
    """Un script s'écrit sur autant de lignes que voulu, avec commentaires ;
    le ``;`` final est toléré."""

    def test_multiline_script_with_comments_is_evaluated(self):
        for payload, expected in [
            ({"Montant": 60, "Canal": "mobile"}, True),
            ({"Montant": 40, "Canal": "mobile"}, False),
            ({"Montant": 60, "Canal": "guichet"}, False),
        ]:
            assert _passes(MULTILINE, payload, "DECIMAL seuil", "seuil = '100'") is expected

    def test_error_points_to_the_line_inside_the_script(self):
        body = MULTILINE.replace("AND @IncomingEvent.Canal", "AND seuill")
        with pytest.raises(InvalidArgumentNameError, match=r"^r\.expr:4:4: .*seuill"):
            _load(body, "DECIMAL seuil", "seuil = '100'")
