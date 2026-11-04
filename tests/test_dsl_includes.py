"""INCLUDE / FRAGMENT : fragments réutilisables et chargement de répertoire."""

from __future__ import annotations

import pytest

from urban_workflow import FunctionRegistry, WorkflowsConfig
from urban_workflow.dsl import (
    WorkflowConfigVisitor,
    WorkflowScriptParser,
    load_directory,
)

FRAGMENT = """
FRAGMENT NAME referentiel
DESCRIPTION 'déclarations communes'
DEFINE EVENT Event1 'incoming event 1';
DEFINE RULE  IsEmpty (TEXT text) 'is empty';
DEFINE CONST agemin 18 'majorité';
"""

MAIN = """
INCLUDE 'referentiel.wf'
NAME wrk1 VERSION 3
DEFINE ACTION Cut (TEXT key) 'remove user';
INITIALIZE WORKFLOW
    ON EVENT Event1 WHEN NOT IsEmpty(text = @Workflow.ExternalId)
        SWITCH State1
DEFINE STATE State1 'state 1'
    ON ENTER STATE EXECUTE Cut(key = @Workflow.ExternalId)
;
"""


def make_visitor() -> WorkflowConfigVisitor:
    rules = FunctionRegistry("rule")
    rules.add("IsEmpty", lambda ctx, text: not text)
    return WorkflowConfigVisitor(rules=rules)


class TestParserMetadata:
    def test_fragment_detection(self):
        parser = WorkflowScriptParser.parse_string(FRAGMENT, filename="referentiel.wf")
        assert parser.is_fragment is True
        assert parser.includes == []

    def test_includes_extraction(self):
        parser = WorkflowScriptParser.parse_string(MAIN, filename="main.wf")
        assert parser.is_fragment is False
        assert parser.includes == ["referentiel.wf"]
        assert parser.crc != 0


class TestFragmentVisit:
    def test_fragment_then_full_script(self):
        visitor = make_visitor()

        fragment = WorkflowScriptParser.parse_string(
            FRAGMENT, filename="referentiel.wf"
        ).check()
        fragment.visit(visitor)

        main = WorkflowScriptParser.parse_string(MAIN, filename="main.wf").check()
        config = main.visit(visitor)

        assert config.name == "wrk1"
        assert config.version == 3
        # Déclarations du fragment disponibles dans le script principal.
        assert "Event1" in config.declared_events
        assert config.declared_events["Event1"].label == "incoming event 1"
        assert "IsEmpty" in visitor.declarations
        assert visitor.constants["agemin"].value == 18
        # La condition WHEN du principal utilise la règle déclarée au fragment.
        assert config.initializers["Event1"].switchs[0].when_rule is not None
        # Le CRC est celui du script principal, pas du fragment.
        assert config.crc == main.crc


class TestLoadDirectory:
    def test_load_directory_resolves_includes(self, tmp_path):
        (tmp_path / "referentiel.wf").write_text(FRAGMENT, encoding="utf-8")
        (tmp_path / "main.wf").write_text(MAIN, encoding="utf-8")

        config = load_directory(WorkflowsConfig(), make_visitor, tmp_path, "*.wf")

        assert len(config) == 1
        document = config.get("wrk1", 3)
        assert "Event1" in document.declared_events
        assert document.states["State1"].incoming_rules[0].actions[0].name == "Cut"

    def test_missing_include_raises(self, tmp_path):
        (tmp_path / "main.wf").write_text(MAIN, encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="referentiel.wf"):
            load_directory(WorkflowsConfig(), make_visitor, tmp_path, "*.wf")
