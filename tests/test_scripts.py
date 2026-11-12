"""Méthodes des règles et actions référencées par ``AS @script``.

Décision utilisateur du 2026-11-07 : le document de workflow ne porte pas
de code ; ``DEFINE RULE``/``DEFINE ACTION`` référencent un script du
ScriptRegistry, multi-langage (``expression``, ``python``, langages
enregistrables). L'exécution des méthodes d'action est à cadrer : la
référence est seulement vérifiée.
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
from urban_workflow.dsl import WorkflowConfigVisitor, WorkflowScriptParser, parse_config
from urban_workflow.dsl.surface import extract_surface, render_script
from urban_workflow.exceptions import (
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
    UnknownScriptError,
)
from urban_workflow.outputs import default_memory_output
from urban_workflow.scripts import Script, ScriptLanguage, ScriptRegistry

SCRIPT = """
NAME Demo
DEFINE EVENT Ouverture 'o';
DEFINE RULE Eleve (DECIMAL seuil) 'montant élevé' AS @montant_eleve;
DEFINE ACTION Notifier (TEXT niveau) 'notification' AS @notifier;
INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN Eleve(seuil = '1000') SWITCH Ouvert
DEFINE STATE Ouvert 'ouvert'
    ON ENTER STATE EXECUTE Notifier(niveau = 'info')
;
"""


def _registry() -> ScriptRegistry:
    return (
        ScriptRegistry()
        .add_script("montant_eleve", "@IncomingEvent.Montant > seuil")
        .add_script("notifier", "TRUE")
    )


def _created(script: str, scripts: ScriptRegistry, payload: dict) -> bool:
    config = parse_config(script, scripts=scripts)
    storage = MemoryStorage()
    processor = WorkflowProcessor(WorkflowsConfig().add_document(config), WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    WorkflowEngine(processor).evaluate_event(
        {"Name": "Ouverture", "Uuid": str(uuid4()), "ExternalId": "K", **payload}
    )
    return bool(storage.get_all(Workflow))


class TestReferences:
    def test_rule_is_evaluated_by_its_script(self):
        assert _created(SCRIPT, _registry(), {"Montant": 1500})
        assert not _created(SCRIPT, _registry(), {"Montant": 500})

    def test_unknown_script_is_positioned_on_the_reference(self):
        scripts = ScriptRegistry().add_script("notifier", "TRUE")
        with pytest.raises(UnknownScriptError, match=r"x\.wf:4:\d+: rule 'Eleve'.*montant_eleve"):
            parse_config(SCRIPT, scripts=scripts, filename="x.wf")

    def test_unknown_action_script_is_rejected(self):
        scripts = ScriptRegistry().add_script("montant_eleve", "TRUE")
        with pytest.raises(UnknownScriptError, match="action 'Notifier'.*notifier"):
            parse_config(SCRIPT, scripts=scripts)

    def test_action_reference_is_kept_on_the_declaration(self):
        parser = WorkflowScriptParser.parse_string(SCRIPT).check()
        visitor = WorkflowConfigVisitor(scripts=_registry())
        parser.visit(visitor)
        assert visitor.declarations["Notifier"].script_ref == "notifier"
        assert visitor.declarations["Eleve"].script_ref == "montant_eleve"

    def test_without_registry_references_are_kept_but_a_call_is_refused(self):
        # Mode permissif (comme les schémas) : la déclaration passe, mais
        # rien ne permet d'évaluer la règle.
        parse_config(SCRIPT.replace("WHEN Eleve(seuil = '1000') ", ""))
        with pytest.raises(InvalidMethodReferenceError, match="no ScriptRegistry"):
            parse_config(SCRIPT)

    def test_dotted_script_names(self):
        script = SCRIPT.replace("@montant_eleve", "@regles.montant")
        scripts = ScriptRegistry().add_script("regles.montant", "TRUE").add_script(
            "notifier", "TRUE"
        )
        assert _created(script, scripts, {})

    def test_one_script_shared_by_two_rules(self):
        script = SCRIPT.replace(
            "DEFINE ACTION",
            "DEFINE RULE Autre (DECIMAL seuil) 'autre' AS @montant_eleve;\nDEFINE ACTION",
        ).replace("WHEN Eleve(seuil = '1000')", "WHEN Eleve(seuil = '1000') AND Autre(seuil = '1')")
        assert _created(script, _registry(), {"Montant": 1500})

    def test_script_checked_against_each_referencing_signature(self):
        script = SCRIPT.replace(
            "DEFINE ACTION",
            "DEFINE RULE Autre (DECIMAL plafond) 'autre' AS @montant_eleve;\nDEFINE ACTION",
        )
        with pytest.raises(InvalidArgumentNameError, match="seuil"):
            parse_config(script, scripts=_registry())


class TestPythonLanguage:
    def test_function_receives_the_typed_arguments(self):
        seen = {}

        def eleve(ctx, seuil):
            seen["seuil"] = seuil
            return ctx.incoming_event.extended_datas["Montant"] > seuil

        scripts = ScriptRegistry().add_function("montant_eleve", eleve).add_script(
            "notifier", "TRUE"
        )
        assert _created(SCRIPT, scripts, {"Montant": 1500})
        assert seen == {"seuil": 1000.0}

    def test_signature_mismatch_is_rejected_at_load(self):
        scripts = ScriptRegistry().add_function(
            "montant_eleve", lambda ctx, plafond: True
        ).add_script("notifier", "TRUE")
        with pytest.raises((InvalidArgumentNameError, MissingArgumentNameError)):
            parse_config(SCRIPT, scripts=scripts)

    def test_script_and_code_rule_under_the_same_name_is_rejected(self):
        rules = FunctionRegistry("rule").add("Eleve", lambda ctx, seuil: True)
        with pytest.raises(DuplicatedArgumentNameError, match="script"):
            parse_config(SCRIPT, rules=rules, scripts=_registry())


class TestRegistry:
    def test_files_and_directories(self, tmp_path):
        (tmp_path / "montant_eleve.expr").write_text(
            "-- seuil\n@IncomingEvent.Montant > seuil\n", encoding="utf-8"
        )
        (tmp_path / "notifier.expr").write_text("TRUE", encoding="utf-8")
        (tmp_path / "lisez-moi.txt").write_text("ignoré", encoding="utf-8")
        scripts = ScriptRegistry().add_directory(tmp_path)
        assert scripts.names() == ["montant_eleve", "notifier"]
        assert scripts.get("notifier").origin.endswith("notifier.expr")
        assert _created(SCRIPT, scripts, {"Montant": 1500})

    def test_unknown_extension_and_duplicates(self, tmp_path):
        path = tmp_path / "x.lua"
        path.write_text("return true", encoding="utf-8")
        with pytest.raises(UnknownScriptError, match=r"\.expr"):
            ScriptRegistry().add_file(path)
        with pytest.raises(DuplicatedArgumentNameError):
            ScriptRegistry().add_script("a", "TRUE").add_script("a", "FALSE")
        with pytest.raises(UnknownScriptError, match="language 'lua'"):
            ScriptRegistry().add_script("a", "x", language="lua")

    def test_custom_language(self):
        class Constant(ScriptLanguage):
            """Langage jouet : le texte 'oui' vaut vrai."""

            name = "constant"
            extensions = (".const",)

            def compile(self, script: Script, binding):
                value = script.source.strip() == "oui"
                return lambda run_ctx, params: value

        scripts = ScriptRegistry()
        scripts.register_language(Constant())
        scripts.add_script("montant_eleve", "oui", language="constant").add_script(
            "notifier", "TRUE"
        )
        assert _created(SCRIPT, scripts, {})


class TestSurface:
    def test_references_survive_the_diagram_round_trip(self):
        model = extract_surface(SCRIPT)
        assert model.rules[0].script == "montant_eleve"
        assert model.actions[0].script == "notifier"
        rendered = render_script(model)
        assert "'montant élevé' AS @montant_eleve;" in rendered
        assert "'notification' AS @notifier;" in rendered
        assert render_script(extract_surface(rendered)) == rendered
        parse_config(rendered, scripts=_registry())
