"""INCLUDE / FRAGMENT : fragments réutilisables et chargement de répertoire."""

from __future__ import annotations

import pytest

from urban_workflow import FunctionRegistry, WorkflowsConfig
from urban_workflow.dsl import (
    WorkflowConfigVisitor,
    WorkflowScriptParser,
    load_directory,
)
from urban_workflow.exceptions import DuplicatedArgumentNameError

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


# ----------------------------------------------------------------------
# Plusieurs fragments pour un même script
# ----------------------------------------------------------------------

FRAGMENT_EVENEMENTS = """
FRAGMENT NAME evenements
DEFINE EVENT EvA 'event a';
DEFINE CONST seuil 18 'majorité';
"""

FRAGMENT_REGLES = """
FRAGMENT NAME regles
DEFINE RULE IsEmpty (TEXT text) 'is empty';
DEFINE ACTION Notifier (TEXT motif) 'notifier';
"""

FRAGMENT_ARTEFACTS = """
FRAGMENT NAME artefacts
DEFINE EVENT EvB 'event b';
DEFINE ARTIFACT Corps 'corps http' USING @corps;
"""

MULTI_MAIN = """
INCLUDE 'evenements.wf'
INCLUDE 'regles.wf'
INCLUDE 'artefacts.wf'
NAME wrk1 VERSION 1
DEFINE CONST local 5 'propre au script';
INITIALIZE WORKFLOW
    ON EVENT EvA WHEN NOT IsEmpty(text = @Workflow.ExternalId) SWITCH State1
DEFINE STATE State1 'state 1'
    ON EVENT EvB
        EXECUTE Notifier(motif = @artifact.Corps)
        SWITCH State1
;
"""

# Second workflow : deux des mêmes fragments, pas celui des artefacts.
MULTI_SECOND = """
INCLUDE 'regles.wf'
INCLUDE 'evenements.wf'
NAME wrk2 VERSION 1
DEFINE CONST autre 7 'autre';
INITIALIZE WORKFLOW
    ON EVENT EvA SWITCH Depart
DEFINE STATE Depart 'départ'
    ON ENTER STATE EXECUTE Notifier(motif = 'bonjour')
;
"""


class TestSeveralFragments:
    """Un script peut empiler autant d'``INCLUDE`` que nécessaire."""

    def _write(self, directory, **files):
        for name, text in files.items():
            (directory / f"{name}.wf").write_text(text, encoding="utf-8")

    def _visitor_factory(self):
        pytest.importorskip("jsonschema")
        from urban_workflow.schemas import SchemaRegistry
        from urban_workflow.scripts import ScriptRegistry

        scripts = ScriptRegistry().add_script(
            "corps", '{"ref": $.IncomingEvent.ExternalId}', language="jslt"
        )

        def factory():
            rules = FunctionRegistry("rule")
            rules.add("IsEmpty", lambda ctx, text: not text)
            return WorkflowConfigVisitor(
                rules=rules, scripts=scripts, schemas=SchemaRegistry()
            )

        return factory

    def test_three_fragments_feed_one_workflow(self, tmp_path):
        factory = self._visitor_factory()
        self._write(tmp_path, evenements=FRAGMENT_EVENEMENTS,
                    regles=FRAGMENT_REGLES, artefacts=FRAGMENT_ARTEFACTS,
                    principal=MULTI_MAIN)

        document = load_directory(
            WorkflowsConfig(), factory, tmp_path, "*.wf"
        ).get("wrk1", 1)

        # Événements des deux fragments qui en déclarent.
        assert {"EvA", "EvB"} <= set(document.declared_events)
        # Artefact du troisième, script résolu, consommé par l'action
        # déclarée dans un quatrième (la branche porte l'EXECUTE).
        assert document.declared_artifacts["Corps"].script_ref == "corps"
        transition = document.states["State1"].events["EvB"].transitions[0]
        assert transition.rule_actions[0].actions[0].name == "Notifier"
        # Règle du deuxième fragment, utilisée par la condition de l'initialiseur.
        assert document.initializers["EvA"].switchs[0].when_rule is not None

    def test_fragments_are_shared_without_leaking_between_workflows(self, tmp_path):
        """Un visiteur neuf par script complet : wrk2 n'hérite pas de wrk1."""
        factory = self._visitor_factory()
        self._write(tmp_path, evenements=FRAGMENT_EVENEMENTS,
                    regles=FRAGMENT_REGLES, artefacts=FRAGMENT_ARTEFACTS,
                    principal=MULTI_MAIN, second=MULTI_SECOND)

        config = load_directory(WorkflowsConfig(), factory, tmp_path, "*.wf")

        assert len(config) == 2
        second = config.get("wrk2", 1)
        assert "EvA" in second.declared_events          # fragment partagé
        assert "EvB" not in second.declared_events      # fragment non inclus
        assert second.declared_artifacts == {}

    def test_same_fragment_twice_is_an_error(self, tmp_path):
        """Pas d'inclusion idempotente : la deuxième visite redéclare."""
        factory = self._visitor_factory()
        self._write(
            tmp_path,
            evenements=FRAGMENT_EVENEMENTS,
            principal=MULTI_MAIN.replace(
                "INCLUDE 'regles.wf'\nINCLUDE 'artefacts.wf'\n",
                "INCLUDE 'evenements.wf'\n",
            ),
        )

        with pytest.raises(DuplicatedArgumentNameError, match="EvA"):
            load_directory(WorkflowsConfig(), factory, tmp_path, "*.wf")

    def test_collision_between_two_fragments_is_positioned(self, tmp_path):
        """L'erreur désigne le fragment fautif, pas le script principal."""
        factory = self._visitor_factory()
        self._write(
            tmp_path,
            evenements=FRAGMENT_EVENEMENTS,
            doublon="FRAGMENT NAME doublon\nDEFINE EVENT EvA 'autre source';\n",
            principal=MULTI_MAIN.replace(
                "INCLUDE 'regles.wf'\nINCLUDE 'artefacts.wf'\n",
                "INCLUDE 'doublon.wf'\n",
            ),
        )

        with pytest.raises(DuplicatedArgumentNameError) as error:
            load_directory(WorkflowsConfig(), factory, tmp_path, "*.wf")
        assert "doublon.wf" in str(error.value)
