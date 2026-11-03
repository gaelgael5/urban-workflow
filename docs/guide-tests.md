# Guide des tests — écrire des règles testables et tester ses workflows

Un workflow se teste à quatre niveaux, du plus rapide au plus intégré :
les **règles métier** seules, la **configuration** produite par un script
DSL, les **templates** de sortie, et le **scénario de bout en bout**
(événements → états → messages). Ce guide donne la recette de chacun,
avec pytest.

## 1. Écrire des règles faites pour être testées

Une règle est un callable `(ctx, **kwargs) -> bool`. Pour qu'elle soit
testable isolément :

- **pure** : elle lit le contexte et retourne un booléen — pas d'I/O, pas
  d'horloge directe (passer par `WorkflowClock.now()` si une date est
  nécessaire), pas de mutation du contexte ;
- **défensive** : une donnée absente du payload est un cas normal
  (retourner `False`), pas une exception ;
- **nommée et typée** : la signature Python est le contrat — c'est contre
  elle que le parseur valide les appels `WHEN` du script.

```python
# regles.py
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("MontantInferieur")
def montant_inferieur(ctx: RunContext, seuil: float) -> bool:
    montant = ctx.incoming_event.extended_datas.get("Montant")
    return montant is not None and float(montant) < seuil
```

### Tester une règle seule

Un `RunContext` se construit à la main — trois dataclasses, aucun moteur :

```python
from urban_workflow import IncomingEvent, RunContext, Workflow

def make_ctx(**payload) -> RunContext:
    return RunContext(
        workflow=Workflow(workflow_name="ValidationAchat", external_id="DA-1"),
        incoming_event=IncomingEvent(name="DemandeSoumise",
                                     extended_datas=dict(payload)),
    )

def test_montant_inferieur():
    assert montant_inferieur(make_ctx(Montant=120), seuil=500.0) is True
    assert montant_inferieur(make_ctx(Montant=900), seuil=500.0) is False
    assert montant_inferieur(make_ctx(), seuil=500.0) is False   # donnée absente
```

Pour une règle qui regarde l'historique (`ctx.workflow.events`), ajouter
des `Event(name=…, to_state=…)` à `workflow.events`.

## 2. Tester un script DSL (la configuration)

`parse_config` transforme le script en `WorkflowConfig` : on vérifie la
**structure** (états, transitions, cibles résolues) et le **comportement
des conditions** compilées, sans faire tourner le moteur.

```python
from urban_workflow.dsl import parse_config
from regles import rules

def test_structure_du_circuit():
    config = parse_config(SCRIPT, rules=rules, filename="validation.wf")

    assert set(config.states) == {
        "Tri", "Incomplete", "EnValidation", "Approuvee", "Rejetee", "Expiree",
    }
    transition = config.states["EnValidation"].events["ValidationAccordee"].transitions[0]
    assert transition.target_state is config.states["Approuvee"]

def test_condition_du_tri():
    config = parse_config(SCRIPT, rules=rules)
    branches = config.states["Tri"].events["DemandeSoumise"].transitions

    # Les closures WHEN s'évaluent directement sur un contexte fabriqué.
    assert branches[0].when_rule(make_ctx()) is True            # incomplet
    assert branches[1].when_rule(make_ctx(Montant=120)) is True # sous le seuil
    assert branches[2].when_rule is None                        # branche par défaut
```

### Tester que le script est bien rejeté

Les erreurs de chargement sont positionnées — les tests peuvent l'exiger :

```python
import pytest
from urban_workflow.exceptions import (
    DslSyntaxError, InvalidMethodReferenceError, MissingStateError,
)

def test_action_non_declaree():
    script = SCRIPT.replace("NotifierValideur(", "Inconnue(")
    with pytest.raises(InvalidMethodReferenceError, match=r"validation\.wf:\d+:\d+"):
        parse_config(script, rules=rules, filename="validation.wf")

def test_erreur_de_syntaxe_positionnee():
    with pytest.raises(DslSyntaxError) as excinfo:
        parse_config("NAME x DEFINE EVENT e 'e'", rules=rules)  # ; manquant
    assert excinfo.value.errors[0].line >= 1
```

### Journal fonctionnel

Chaque évaluation de règle trace une ligne dans
`ctx.functional_log` (`MontantInferieur(seuil=500.0) -> True`) : utile en
assertion pour vérifier *pourquoi* une branche a été prise.

## 3. Tester les templates de sortie

Un template se teste en triplet *document de contexte → template →
résultat*, sans moteur :

```python
from urban_workflow.templating import TemplateRegistry, build_action_document

def test_template_notifier_valideur():
    registry = TemplateRegistry().add_directory("templates/")

    ctx = make_ctx(Montant=900)
    action = config_action_notifier.map(ctx)     # ResultActionConfig.map
    body = registry.transform("NotifierValideur",
                              build_action_document(ctx, action))

    assert body == {
        "Ordre": "notifier",
        "Dossier": "DA-1",
        "Montant": 900,
    }
```

Pour des sorties datées reproductibles, figer l'horloge (voir §5).

## 4. Tester un scénario de bout en bout

Le trio `MemoryStorage` + `default_memory_output` + `WorkflowEngine`
donne un moteur complet en mémoire, sans infrastructure :

```python
from uuid import uuid4

from urban_workflow import (
    MemoryStorage, PushedAction, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output
import pytest

@pytest.fixture
def moteur():
    storage = MemoryStorage()
    configs = WorkflowsConfig().add_document(parse_config(SCRIPT, rules=rules))
    processor = WorkflowProcessor(configs, WorkflowFactory())
    processor.load_existing_workflows_by_external_id = (
        lambda key: storage.get_by(Workflow, key, "external_id")
    )
    processor.output_actions = default_memory_output(storage)
    return WorkflowEngine(processor), storage

def evenement(nom, dossier, **donnees):
    return {"Name": nom, "Uuid": str(uuid4()), "ExternalId": dossier,
            "Type": "achat", **donnees}

def test_approbation_automatique(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-1", Montant=120))

    dossier = storage.get_by(Workflow, "DA-1", "external_id")[0]
    assert dossier.current_state == "Approuvee"
    assert dossier.extended_datas["Statut"] == "approuvee"      # STORE

def test_refus(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-2", Montant=900))
    engine.evaluate_event(evenement("ValidationRefusee", "DA-2",
                                    Motif="budget épuisé"))

    dossier = storage.get_by(Workflow, "DA-2", "external_id")[0]
    assert dossier.current_state == "Rejetee"
    # Le message poussé au refus porte le motif de l'événement entrant.
    notification = next(a for a in dossier.last_event.actions
                        if a.name == "NotifierDemandeur")
    assert notification.execute_message["Body"]["Arguments"]["motif"] == "budget épuisé"
```

### Tester une expiration

L'expiration se simule en rejouant soi-même le rappel, comme le ferait le
bus différé :

```python
def test_expiration(moteur):
    engine, storage = moteur
    engine.evaluate_event(evenement("DemandeSoumise", "DA-3", Montant=900))
    dossier = storage.get_by(Workflow, "DA-3", "external_id")[0]
    assert dossier.current_state == "EnValidation"

    # Le rappel différé a été poussé sur le bus à l'entrée de l'état.
    rappel = storage.get_all(PushedAction)[-1]
    assert rappel.execute_message["Body"]["Delay"] == 3 * 24 * 60

    # À l'échéance, le bus renverrait l'événement __expired :
    engine.evaluate_event(evenement(
        "__expired", "DA-3",
        WorkflowId=str(dossier.uuid), CurrentState="EnValidation",
    ))
    dossier = storage.get_by(Workflow, "DA-3", "external_id")[0]
    assert dossier.current_state == "Expiree"
```

Et le rappel périmé (l'état a changé entre-temps) doit être sans effet —
un `CurrentState` différent de l'état réel laisse le workflow en place.

## 5. Maîtriser le temps

Tout le moteur date ses objets via `WorkflowClock.now()`. Pour des tests
déterministes :

```python
from datetime import datetime, timezone
from urban_workflow import WorkflowClock

NOW = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)

def test_date_de_sortie_figee(moteur):
    engine, storage = moteur
    with WorkflowClock.frozen(NOW):
        engine.evaluate_event(evenement("DemandeSoumise", "DA-4", Montant=120))
    action = storage.get_all(PushedAction)[0]
    assert action.execute_message["Body"]["PushedAt"] == NOW.isoformat()
```

`WorkflowClock.set_provider(...)` / `reset()` existent pour un contrôle
plus fin (horloge qui avance pas à pas).

## 6. Pièges et idiomes

- **Un `Uuid` d'événement neuf par envoi** : le moteur ignore un uuid déjà
  intégré (protection de rejeu). Un test qui réutilise le même uuid
  « ne fait rien » la deuxième fois — c'est voulu.
- **`MATCHING` s'applique à la création** : un événement de test sans les
  paires du filtre ne crée pas d'instance — penser à les inclure dans la
  fabrique d'événements du test.
- **Tester le kind, pas l'implémentation** : `EXECUTE` → `$_push`,
  `STORE` → `$_update`, kind personnalisé → tel quel. La chaîne de
  sorties se teste en vérifiant `storage.get_all(PushedAction)` et les
  `extended_datas` du workflow.
- **Transactions** : pour tester un maillon de sortie custom, faire
  échouer `_execute_impl` et vérifier que le rollback a eu lieu et que
  l'exception remonte (le moteur annule toute la chaîne).
- **Suite de référence** : les tests du dépôt sont eux-mêmes des exemples
  complets — `tests/test_dsl.py` (golden du langage),
  `tests/test_engine.py` (moteur), `tests/test_engine_dsl.py` (bout en
  bout DSL), `tests/test_templating.py` (templates).
