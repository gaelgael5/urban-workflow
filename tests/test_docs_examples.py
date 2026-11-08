"""Les exemples de la documentation restent vrais.

Ce module rejoue le cas d'usage complet des guides (`docs/guide-dsl.md` §6,
`docs/guide-integration.md`, `docs/guide-tests.md`) : le circuit de
validation des demandes d'achat. Si un guide doit changer, ce test change
avec lui — et réciproquement.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from urban_workflow import (
    FunctionRegistry,
    MemoryStorage,
    PushedAction,
    Workflow,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output

SCRIPT = """
NAME ValidationAchat VERSION 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise     'une demande est déposée';
DEFINE EVENT  PiecesFournies     'le demandeur complète son dossier';
DEFINE EVENT  ValidationAccordee 'un valideur approuve';
DEFINE EVENT  ValidationRefusee  'un valideur refuse';

DEFINE RULE   EstComplet (TEXT champs)         'les champs requis sont présents';
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil';

DEFINE ACTION NotifierValideur (TEXT niveau, TEXT dossier)  'demande d''approbation';
DEFINE ACTION NotifierDemandeur (TEXT motif, TEXT dossier)  'information du demandeur';

DEFINE CONST  seuil_auto 500 'approbation automatique sous ce montant';

INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            EXECUTE NotifierDemandeur(motif = 'dossier incomplet',
                                      dossier = @Workflow.ExternalId)
            SWITCH Incomplete
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        EXECUTE NotifierValideur(niveau = 'standard',
                                 dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;

DEFINE STATE Incomplete 'en attente de pièces'
    ON EVENT PiecesFournies
        WHEN EstComplet(champs = 'Montant')
            EXECUTE NotifierValideur(niveau = 'standard',
                                     dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;

DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        SWITCH Approuvee
    ON EVENT ValidationRefusee
        EXECUTE NotifierDemandeur(motif = @IncomingEvent.Motif,
                                  dossier = @Workflow.ExternalId)
        SWITCH Rejetee
    EXPIRE AFTER 3 DAY
        SWITCH Expiree
;

DEFINE STATE Approuvee 'demande approuvée'
    ON ENTER STATE
        STORE (Statut = 'approuvee')
;

DEFINE STATE Rejetee 'demande rejetée'
    ON ENTER STATE
        STORE (Statut = 'rejetee')
;

DEFINE STATE Expiree 'validation expirée sans réponse'
    ON ENTER STATE
        EXECUTE NotifierValideur(niveau = 'relance',
                                 dossier = @Workflow.ExternalId)
;
"""


def make_rules() -> FunctionRegistry:
    rules = FunctionRegistry("rule")
    rules.add(
        "EstComplet",
        lambda ctx, champs: all(
            ctx.incoming_event.extended_datas.get(c) is not None
            for c in champs.split(",")
        ),
    )
    rules.add(
        "MontantInferieur",
        lambda ctx, seuil: float(ctx.incoming_event.extended_datas.get("Montant", 0))
        < seuil,
    )
    return rules


@pytest.fixture
def moteur():
    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(
        parse_config(SCRIPT, rules=make_rules(), filename="validation.wf")
    )
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
        Workflow, key, "external_id"
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage


def evenement(nom: str, dossier: str, **donnees):
    return {
        "Name": nom,
        "Uuid": str(uuid4()),
        "ExternalId": dossier,
        "Type": "achat",
        **donnees,
    }


def etat(storage: MemoryStorage, dossier: str) -> Workflow:
    return storage.get_by(Workflow, dossier, "external_id")[0]


class TestCircuitDeValidation:
    def test_approbation_automatique_sous_le_seuil(self, moteur):
        engine, storage = moteur
        engine.evaluate_event(evenement("DemandeSoumise", "DA-1", Montant=120))

        dossier = etat(storage, "DA-1")
        assert dossier.current_state == "Approuvee"
        assert dossier.extended_datas["Statut"] == "approuvee"  # STORE

    def test_dossier_incomplet_puis_complete(self, moteur):
        engine, storage = moteur
        engine.evaluate_event(evenement("DemandeSoumise", "DA-2"))
        assert etat(storage, "DA-2").current_state == "Incomplete"

        engine.evaluate_event(evenement("PiecesFournies", "DA-2", Montant=900))
        assert etat(storage, "DA-2").current_state == "EnValidation"

    def test_refus_avec_motif(self, moteur):
        engine, storage = moteur
        engine.evaluate_event(evenement("DemandeSoumise", "DA-3", Montant=900))
        engine.evaluate_event(
            evenement("ValidationRefusee", "DA-3", Motif="budget épuisé")
        )

        dossier = etat(storage, "DA-3")
        assert dossier.current_state == "Rejetee"
        assert dossier.extended_datas["Statut"] == "rejetee"

        notification = next(
            action
            for action in dossier.last_event.actions
            if action.name == "NotifierDemandeur"
        )
        arguments = notification.execute_message["Body"]["Arguments"]
        assert arguments == {"motif": "budget épuisé", "dossier": "DA-3"}

    def test_expiration_et_rappel_perime(self, moteur):
        engine, storage = moteur
        engine.evaluate_event(evenement("DemandeSoumise", "DA-4", Montant=900))
        dossier = etat(storage, "DA-4")
        assert dossier.current_state == "EnValidation"

        # Le rappel différé (3 jours) a été poussé à l'entrée de l'état.
        rappel = storage.get_all(PushedAction)[-1]
        assert rappel.execute_message["Body"]["Delay"] == 3 * 24 * 60

        # Un rappel périmé (l'état indiqué ne correspond plus) est ignoré.
        engine.evaluate_event(
            evenement(
                "__expired", "DA-4", WorkflowId=str(dossier.uuid), CurrentState="Tri"
            )
        )
        assert etat(storage, "DA-4").current_state == "EnValidation"

        # Le rappel à l'heure applique la transition d'expiration.
        engine.evaluate_event(
            evenement(
                "__expired",
                "DA-4",
                WorkflowId=str(dossier.uuid),
                CurrentState="EnValidation",
            )
        )
        assert etat(storage, "DA-4").current_state == "Expiree"

    def test_filtre_matching(self, moteur):
        engine, storage = moteur
        payload = evenement("DemandeSoumise", "DA-5", Montant=120)
        payload["Type"] = "conge"  # ne passe pas MATCHING (Type = 'achat')
        engine.evaluate_event(payload)
        assert storage.get_by(Workflow, "DA-5", "external_id") == []

    def test_branches_du_tri(self):
        config = parse_config(SCRIPT, rules=make_rules())
        branches = config.states["Tri"].events["DemandeSoumise"].transitions
        assert branches[0].when_rule is not None
        assert branches[1].when_rule is not None
        assert branches[2].when_rule is None  # branche par défaut
        assert [b.target_state_name for b in branches] == [
            "Incomplete",
            "Approuvee",
            "EnValidation",
        ]


# ----------------------------------------------------------------------
# Les blocs de code du guide d'intégration s'exécutent TELS QU'ÉCRITS
# ----------------------------------------------------------------------

from pathlib import Path  # noqa: E402

GUIDE = Path(__file__).resolve().parent.parent / "docs" / "guide-integration.md"


def _python_block(heading: str) -> str:
    """Premier bloc ```python qui suit le titre ``heading`` du guide."""
    text = GUIDE.read_text(encoding="utf-8")
    after = text[text.index(heading):]
    start = after.index("```python\n") + len("```python\n")
    return after[start:after.index("\n```", start)]


class TestGuideIntegration:
    def test_exemple_complet_de_bout_en_bout(self, capsys):
        pytest.importorskip("yaml")
        pytest.importorskip("jsonschema")
        exec(compile(_python_block("## 9. Exemple complet"), "guide-integration §9", "exec"), {})
        lines = capsys.readouterr().out.splitlines()
        assert lines[0] == "Facturee"
        assert lines[1].startswith('AlerterCommercial {"Header": {"canal": "bus-commandes"}')
        assert lines[2].endswith(
            '"corps": {"reference": "CMD-1", "client": "ACME", "montant": 1500, '
            '"devise": "EUR"}}}'
        )
        assert lines[3] == "refusé : [\"<racine>: 'Client' is a required property\"]"
        assert lines[4] == "interrompu : ['montant: 0 is less than or equal to the minimum of 0']"
        assert lines[5] == "[]"

    def test_recapitulatif_des_imports(self):
        block = _python_block("## 10. Récapitulatif des imports")
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            # Job CI sans l'extra [sql] : la dernière ligne ne peut pas marcher.
            block = "\n".join(
                line for line in block.splitlines() if "storage_sql" not in line
            )
        exec(compile(block, "guide-integration §10", "exec"), {})
