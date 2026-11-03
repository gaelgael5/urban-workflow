# Guide d'intégration — utiliser un workflow dans du code

Ce document montre comment charger des scripts DSL, implémenter les
règles métier, assembler le moteur, traiter les événements et récupérer
les sorties. Le langage lui-même est décrit dans
[guide-dsl.md](guide-dsl.md), les tests dans
[guide-tests.md](guide-tests.md).

## 1. Démarrage rapide

```python
from urban_workflow import (
    FunctionRegistry, MemoryStorage, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.outputs import default_memory_output

# 1. Les règles métier : des callables (ctx, **kwargs) -> bool
rules = FunctionRegistry("rule")
rules.add("EstComplet", lambda ctx, champs: all(
    ctx.incoming_event.extended_datas.get(c) is not None
    for c in champs.split(",")
))
rules.add("MontantInferieur", lambda ctx, seuil: float(
    ctx.incoming_event.extended_datas.get("Montant", 0)
) < seuil)

# 2. Charger et valider le script DSL
script = open("workflows/validation.wf", encoding="utf-8").read()
config = parse_config(script, rules=rules, filename="validation.wf")

# 3. Assembler le moteur
storage = MemoryStorage()
configs = WorkflowsConfig().add_document(config)

processor = WorkflowProcessor(configs, WorkflowFactory())
processor.load_existing_workflows_by_external_id = (
    lambda key: storage.get_by(Workflow, key, "external_id")
)
processor.output_actions = default_memory_output(storage)

engine = WorkflowEngine(processor)

# 4. Traiter un événement
engine.evaluate_event({
    "Name": "DemandeSoumise",
    "Uuid": "4f6c6c6f-0000-4000-8000-000000000001",
    "ExternalId": "DA-2026-0042",     # l'identifiant du sujet traité
    "EventDate": "2026-11-03T10:00:00+00:00",
    "Type": "achat",                  # consommé par MATCHING
    "Montant": 120,                   # données métier
})

dossier = storage.get_by(Workflow, "DA-2026-0042", "external_id")[0]
print(dossier.current_state)          # "Approuvee" (120 < seuil_auto)
```

## 2. Les règles métier

Une règle est un callable `(ctx, **kwargs) -> bool`. Le premier paramètre
est toujours le `RunContext` ; les suivants sont les arguments nommés de
l'appel DSL, déjà résolus (littéraux convertis au type déclaré, chemins
`@…` lus dans le contexte, constantes substituées).

```python
from urban_workflow import FunctionRegistry, RunContext

rules = FunctionRegistry("rule")

@rules.register("MontantInferieur")
def montant_inferieur(ctx: RunContext, seuil: float) -> bool:
    montant = ctx.incoming_event.extended_datas.get("Montant")
    return montant is not None and float(montant) < seuil
```

Ce que le contexte expose :

| Attribut | Contenu |
|---|---|
| `ctx.incoming_event` | L'événement entrant (`name`, `external_id`, `event_date`, `extended_datas` = le payload) |
| `ctx.workflow` | L'instance (`current_state`, `events` = l'historique, `extended_datas` = l'état métier écrit par `STORE`) |
| `ctx.event` | L'événement en cours d'intégration (`from_state`, `to_state`) |
| `ctx.functional_log` | Journal des évaluations de règles (audit) |

La validation des appels (`WHEN MontantInferieur(seuil = …)`) se fait
contre la **signature du callable** au chargement du script : un argument
inconnu ou manquant est une erreur de chargement, pas d'exécution.

Bonnes pratiques (détaillées dans [guide-tests.md](guide-tests.md)) :
règles **pures** (pas d'I/O), qui lisent le contexte et retournent un
booléen ; tout effet de bord passe par les actions.

## 3. Charger les scripts

### Un script seul

```python
from urban_workflow.dsl import parse_config

config = parse_config(script_text, rules=rules, filename="validation.wf")
```

`parse_config` lève les erreurs positionnées du
[guide-dsl.md](guide-dsl.md) §10. Le `filename` ne sert qu'aux messages.

### Un répertoire avec fragments

```python
from urban_workflow import WorkflowsConfig
from urban_workflow.dsl import WorkflowConfigVisitor, load_directory

def visitor_factory():
    return WorkflowConfigVisitor(rules=rules)

configs = load_directory(WorkflowsConfig(), visitor_factory, "workflows/", "*.wf")
```

Les fichiers `FRAGMENT` sont visités avant les scripts qui les
`INCLUDE` ; chaque script complet devient un document de `configs`.

### Contrôle fin

```python
from urban_workflow.dsl import WorkflowScriptParser, WorkflowConfigVisitor

parser = WorkflowScriptParser.parse_string(script_text, filename="x.wf")
parser.check()                 # lève DslSyntaxError si erreurs de syntaxe
parser.includes                # fichiers INCLUDE déclarés
parser.is_fragment             # script FRAGMENT ?
config = parser.visit(WorkflowConfigVisitor(rules=rules))
```

## 4. Les sorties : actions, templates, en-têtes

Quand une branche déclenche `EXECUTE Action(…)`, le moteur collecte
l'action puis la **matérialise** en message via un `ActionTranslator`.
Deux implémentations :

- `DefaultActionTranslator` (par défaut) : corps JSON générique, sans
  configuration ;
- `JsltActionTranslator` : corps produit par un **template JSLT
  urban-json** par nom d'action — la voie recommandée.

```python
from urban_workflow.templating import (
    JsltActionTranslator, MetadataRegistry, TemplateRegistry,
)

templates = TemplateRegistry().add_directory("templates/")   # *.jslt
metadatas = MetadataRegistry(default={"canal": "bus-achats"})
metadatas.add_metadata("NotifierValideur", {"canal": "mail", "ttl": "3600"})

processor = WorkflowProcessor(
    configs, WorkflowFactory(),
    translator=JsltActionTranslator(templates, metadatas),
)
```

### Les templates `.jslt`

Un fichier par nom d'action (`NotifierValideur.jslt`), `default.jslt`
pour le repli. Le template navigue dans le **document de contexte** de
l'action :

```jslt
{
    "Ordre":     "notifier",
    "Niveau":    $.action.arguments.niveau,
    "Dossier":   $.workflow.external_id,
    "Etat":      $.workflow.state,
    "Montant":   $.incoming.Montant,
    "EmisLe":    $.now
}
```

Sections disponibles : `$.action` (uuid, name, kind, delay, arguments
résolus), `$.workflow` (uuid, name, version, external_id, state + données
étendues), `$.event` (uuid, name, from_state, to_state + données),
`$.incoming` (uuid, name, external_id, dates + payload), `$.now`.

Sans template dédié ni `default.jslt`, le template par défaut intégré
produit la forme historique du moteur source : `Uuid`, `Name`,
`PushedAt`, `Arguments`, `WorkflowId`, `EventId`, `From_State`,
`To_State`.

Des fonctions urban-json personnalisées peuvent être exposées aux
templates :

```python
from urban_json import default_registry

functions = default_registry.copy()
functions.register("majuscules", lambda ctx, v: str(v).upper())
templates = TemplateRegistry(functions=functions)
```

### Le message produit

Chaque action matérialisée est une `PushedAction` accrochée à l'événement
d'historique, avec `execute_message = {"Header": …, "Body": …}` :
`Header` vient du `MetadataRegistry` (en-têtes de routage), `Body` du
template. Une action différée (`WAITING`, rappel d'expiration) a un corps
enveloppé : `{"Name": "$_reminder", "Delay": minutes, "Message": corps}`.

## 5. La chaîne de sorties et la persistance

À chaque évaluation, le processeur fabrique une **chaîne de sorties**
(pattern décorateur) et l'exécute sous transaction :

```python
processor.output_actions = default_memory_output(storage)
# équivaut à :
#   SetPropertiesOutputAction(        # applique les STORE au workflow
#       PushBusOutputAction(storage,  # pousse les $_push vers le "bus"
#           PushModelOutputAction(storage)))  # persiste le workflow
```

Le cœur ne fait **aucune E/S** : brancher une vraie infrastructure, c'est
fournir deux points d'extension —

1. `processor.load_existing_workflows_by_external_id` : charger les
   instances d'un sujet depuis votre stockage ;
2. `processor.output_actions` : une fabrique de chaîne dont vos maillons
   héritent d'`OutputAction` (et de `Transaction` pour un commit/rollback
   réel) :

```python
from urban_workflow import OutputAction, Transaction

class PushToRabbit(OutputAction):
    def _prepare_impl(self, ctx):
        self.items.extend(a for a in ctx.event.actions if a.kind == "$_push")
    def _execute_impl(self):
        for action in self.items:
            channel.publish(json.dumps(action.execute_message))
    def _begin_transaction_impl(self):
        return RabbitTransaction(channel)
```

Si un maillon échoue, la transaction de toute la chaîne est annulée et
l'exception remonte — l'événement pourra être rejoué sans doublon.

### Persistance SQL prête à l'emploi (extra `[sql]`)

Pour un déploiement durable sans écrire ses propres maillons, l'extra
`sql` (`pip install urban-workflow[sql]`) fournit un stockage SQLAlchemy
Core — SQLite en développement, PostgreSQL ou autre en production :

```python
from sqlalchemy import create_engine
from urban_workflow.storage_sql import SqlWorkflowStorage, sql_output

storage = SqlWorkflowStorage(create_engine("sqlite:///workflows.db"))
storage.create_schema()    # tables workflows / workflow_events / workflow_actions

processor.load_existing_workflows_by_external_id = storage.load_by_external_id
processor.output_actions = sql_output(storage)
```

Les trois tables reprennent le schéma logique du moteur source ; chaque
workflow est persisté en agrégat (instance, historique d'événements,
actions matérialisées avec leurs messages JSON — l'outbox). Les écritures
sont idempotentes (rejouer une sauvegarde ne duplique rien) et toute la
chaîne partage **une seule transaction SQL** : si un maillon échoue, rien
n'est écrit.

Pour pousser aussi vers un broker, brancher une implémentation de
`OutputBus` :

```python
from urban_workflow.outputs import OutputBus

class RabbitBus(OutputBus):
    def push(self, action):
        channel.publish(json.dumps(action.execute_message))

processor.output_actions = sql_output(storage, bus=RabbitBus())
```

Attention au verrouillage : `MemoryLocker` ne protège qu'un processus.
Plusieurs instances du moteur sur la même base exigent un `LockObject`
distribué (verrou base de données, Redis…).

## 6. Les événements côté moteur

### Format des payloads

`engine.evaluate_event(...)` accepte un JSON (chaîne), un dict, ou un
`IncomingEvent` déjà construit. Propriétés reconnues (CamelCase, héritées
du format source) :

| Clé | Rôle |
|---|---|
| `Name` | Nom de l'événement (obligatoire pour router) |
| `Uuid` | Identité de l'événement — **la clé du rejeu sans doublon** |
| `ExternalId` | Identifiant du sujet : regroupe les instances |
| `CreationDate`, `EventDate` | Dates ISO 8601 |
| *tout le reste* | Données métier (`extended_datas`), visibles des règles, des `MATCHING` et des templates |

Un payload invalide lève `InvalidIncomingEventFormatError`.

### Verrouillage

Le moteur sérialise les traitements d'un même sujet : la clé
(`ExternalId` par défaut, personnalisable via `thread_safe_key`) est
verrouillée pendant l'évaluation (`MemoryLocker` en mémoire ; implémenter
`LockObject` pour un verrou distribué). Un verrou non obtenu dans le
délai lève `LockFailedError`.

### Événements techniques

| Événement | Émis par | Effet |
|---|---|---|
| `__expired` | Votre bus de rappel, à l'échéance d'un `EXPIRE AFTER` (avec `WorkflowId` et `CurrentState`) | Applique la transition d'expiration si l'état n'a pas changé |
| `__cancelReminderAction` | Le moteur, à la sortie d'un état expirable | À interpréter par votre bus : annuler le rappel en attente |
| `$_result` | Votre infrastructure, pour rapporter le résultat d'une action poussée (avec `EventId` et `TaskId`) | Accroche le résultat à la `PushedAction` d'origine, sans entrée d'historique |
| `$_reminder` | — (c'est l'enveloppe des actions différées poussées) | Votre bus la rejoue après `Delay` minutes |

Le contrat du bus de rappel : recevoir les messages `$_reminder`, et à
l'échéance, renvoyer leur `Message` interne comme événement entrant.

## 7. Plusieurs workflows, plusieurs versions

```python
configs = (
    WorkflowsConfig()
    .add_document(parse_config(script_achats_v1, rules=rules))
    .add_document(parse_config(script_achats_v2, rules=rules))
    .add_document(parse_config(script_conges, rules=rules))
)

# Les nouvelles instances "CircuitAchats" ne se créent qu'en v2 ;
# les instances v1 existantes continuent sur leur configuration.
configs.set_version_selector("CircuitAchats", 2)
```

Le routage d'un événement : les filtres `MATCHING` sélectionnent les
workflows candidats à la **création** ; les instances **existantes** sont
retrouvées par `ExternalId` et traitées avec la configuration de leur
version d'origine. Un même événement peut donc impacter plusieurs
workflows à la fois.

## 8. Récapitulatif des imports

```python
from urban_workflow import (            # cœur, sans dépendance lourde
    FunctionRegistry, RunContext, Workflow, IncomingEvent,
    WorkflowsConfig, WorkflowFactory, WorkflowProcessor, WorkflowEngine,
    MemoryStorage, MemoryLocker, OutputAction, Transaction,
    WorkflowClock, constants,
)
from urban_workflow.dsl import (        # parseur ANTLR (le DSL)
    parse_config, load_directory, WorkflowScriptParser, WorkflowConfigVisitor,
)
from urban_workflow.templating import ( # urban-json (templates JSLT)
    JsltActionTranslator, TemplateRegistry, MetadataRegistry,
)
from urban_workflow.outputs import default_memory_output
```

`dsl` et `templating` sont des sous-paquets volontairement non réexportés
par la racine : on ne paie leur coût d'import que si on les utilise.
