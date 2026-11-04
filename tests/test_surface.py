"""Modèle de surface du DSL : extraction fidèle + rendu canonique (point fixe)."""

from __future__ import annotations

import pytest

from urban_workflow import FunctionRegistry
from urban_workflow.dsl import (
    SurfaceError,
    SurfaceModel,
    extract_surface,
    parse_config,
    render_script,
)

SCRIPT = """
NAME ValidationAchat VERSION 2
CONCURENCY 3
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise 'une demande est déposée'
    AS @schema_Demande UNIQUE (ExternalId, Montant);
DEFINE EVENT  PiecesFournies 'le demandeur complète son dossier';
DEFINE EVENT  ValidationAccordee 'un valideur approuve';
DEFINE RULE   EstComplet (TEXT champs) 'les champs requis sont présents';
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil';
DEFINE ACTION Notifier (TEXT cible, TEXT motif) 'notification';
DEFINE CONST  seuil_auto 500 'approbation automatique sous ce montant';

INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise WHEN EstComplet(champs = 'Montant') RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON ENTER STATE
        EXECUTE Notifier(cible = 'journal', motif = 'entrée Tri')
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            EXECUTE Notifier(cible = @Workflow.ExternalId,
                             motif = 'dossier incomplet')
            SWITCH Incomplete
        WHEN EstComplet(champs = 'Montant')
             AND MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        SWITCH EnValidation
;

DEFINE STATE Incomplete 'en attente de pièces'
    ON EVENT PiecesFournies
        WHEN EstComplet(champs = 'Montant')
            SWITCH EnValidation
;

DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        STORE (Statut = 'approuvee')
        SWITCH Approuvee
    EXPIRE AFTER 3 DAY
        EXECUTE Notifier(cible = 'relance', motif = 'délai dépassé')
        SWITCH Expiree
;

DEFINE STATE Expiree 'délai dépassé'
;

DEFINE STATE Approuvee 'terminé'
    ON EXIT STATE
        EXECUTE Notifier(cible = 'audit', motif = 'sortie inattendue')
;
"""


def _registry() -> FunctionRegistry:
    rules = FunctionRegistry("rule")
    rules.add("EstComplet", lambda ctx, champs: True)
    rules.add("MontantInferieur", lambda ctx, seuil: True)
    return rules


class TestExtraction:
    def test_header(self):
        model = extract_surface(SCRIPT)
        assert model.name == "ValidationAchat"
        assert model.version == 2
        assert model.concurrency == 3
        assert model.description == "circuit de validation des demandes d'achat"
        assert model.filters == [{"key": "Type", "value": "achat"}]

    def test_declarations(self):
        model = extract_surface(SCRIPT)
        demande = model.events[0]
        assert demande.name == "DemandeSoumise"
        assert demande.schema_ref == "schema_Demande"
        assert demande.unique == ["ExternalId", "Montant"]
        assert model.events[1].schema_ref == ""

        assert [r.name for r in model.rules] == ["EstComplet", "MontantInferieur"]
        assert model.rules[1].params == [{"type": "DECIMAL", "name": "seuil"}]
        assert model.actions[0].params == [
            {"type": "TEXT", "name": "cible"},
            {"type": "TEXT", "name": "motif"},
        ]
        assert model.consts[0].value == "500"

    def test_initializers_and_states(self):
        model = extract_surface(SCRIPT)
        init = model.initializers[0]
        assert (init.event, init.switch, init.recursive) == (
            "DemandeSoumise",
            "Tri",
            True,
        )
        assert init.when == "EstComplet(champs = 'Montant')"

        tri = model.states[0]
        assert tri.actions[0].trigger == "ENTER"
        assert tri.actions[0].execute.startswith("EXECUTE Notifier(")

        branches = tri.handlers[0].transitions
        assert [b.switch for b in branches] == [
            "Incomplete",
            "Approuvee",
            "EnValidation",
        ]
        assert branches[0].when.startswith("NOT EstComplet")
        # Snippet multi-ligne : continuation désindentée relativement.
        assert "\n" in branches[0].executes[0]
        assert branches[2].when == ""  # branche par défaut

        en_validation = model.states[2]
        assert en_validation.handlers[0].transitions[0].executes[0].startswith(
            "STORE"
        )
        assert en_validation.handlers[1].expire_after == "3 DAY"
        assert model.states[4].actions[0].trigger == "EXIT"

    def test_fragment_and_include_refused(self):
        with pytest.raises(SurfaceError):
            extract_surface("FRAGMENT NAME F DEFINE EVENT E 'e';")
        with pytest.raises(SurfaceError):
            extract_surface(
                "INCLUDE 'commun.wf'\nNAME X\nDEFINE EVENT E 'e';"
            )


class TestRendering:
    def test_fixed_point(self):
        first = render_script(extract_surface(SCRIPT))
        second = render_script(extract_surface(first))
        assert first == second

    def test_roundtrip_preserves_semantics(self):
        rendered = render_script(extract_surface(SCRIPT))
        original = parse_config(SCRIPT, rules=_registry())
        reparsed = parse_config(rendered, rules=_registry())

        assert reparsed.name == original.name
        assert reparsed.version == original.version
        assert reparsed.concurrency == original.concurrency
        assert dict(reparsed.filters) == dict(original.filters)
        assert set(reparsed.states) == set(original.states)
        assert set(reparsed.initializers) == set(original.initializers)
        assert (
            reparsed.declared_events["DemandeSoumise"].dedup_keys
            == original.declared_events["DemandeSoumise"].dedup_keys
        )

        for name, state in original.states.items():
            other = reparsed.states[name]
            for event_name, event in state.events.items():
                targets = [t.target_state_name for t in event.transitions]
                guards = [t.when_rule_text for t in event.transitions]
                other_event = other.events[event_name]
                assert [
                    t.target_state_name for t in other_event.transitions
                ] == targets
                # Les gardes gardent leur texte (au repli des espaces près).
                assert [
                    " ".join(t.when_rule_text.split())
                    for t in other_event.transitions
                ] == [" ".join(g.split()) for g in guards]

    def test_dict_roundtrip(self):
        model = extract_surface(SCRIPT)
        rebuilt = SurfaceModel.from_dict(model.to_dict())
        assert render_script(rebuilt) == render_script(model)

    def test_render_hand_built_model(self):
        """Le modèle minimal qu'enverrait la vue diagramme compile."""
        model = SurfaceModel.from_dict(
            {
                "name": "Demo",
                "events": [{"name": "Ouverture", "label": "ouverture"}],
                "actions": [
                    {
                        "name": "Notifier",
                        "label": "notification",
                        "params": [{"type": "TEXT", "name": "cible"}],
                    }
                ],
                "initializers": [
                    {"event": "Ouverture", "switch": "Ouvert"}
                ],
                "states": [
                    {
                        "name": "Ouvert",
                        "label": "ouvert",
                        "handlers": [
                            {
                                "event": "Ouverture",
                                "transitions": [
                                    {
                                        "executes": [
                                            "EXECUTE Notifier(cible = 'x')"
                                        ],
                                        "switch": "Ouvert",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        config = parse_config(render_script(model), rules=FunctionRegistry("rule"))
        assert set(config.states) == {"Ouvert"}
        assert "Ouverture" in config.initializers

    def test_label_quotes_escaped(self):
        model = SurfaceModel.from_dict(
            {
                "name": "X",
                "description": "l'apostrophe",
                "events": [{"name": "E", "label": "d'accord"}],
                "states": [{"name": "S", "label": ""}],
            }
        )
        rendered = render_script(model)
        assert "l''apostrophe" in rendered
        reparsed = extract_surface(rendered)
        assert reparsed.description == "l'apostrophe"
        assert reparsed.events[0].label == "d'accord"
