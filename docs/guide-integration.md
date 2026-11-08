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

Ce démarrage n'utilise que des règles de code. Le §9 assemble **tout** le
chemin (schémas, scripts de règles, artefact JSON, templates des messages)
dans un exemple complet qui s'exécute tel quel.

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
| `ctx.workflow.states` | Les instances d'état déjà historisées (`StateInstance` : `name`, `uuid`, `creation_date`, `event_id`), une par `SWITCH` |
| `ctx.pending_states` | Les instances créées par les `SWITCH` de l'évaluation en cours, pas encore historisées (une règle `RECURSIVE` les voit déjà) |
| `ctx.functional_log` | Journal des évaluations de règles (audit) |

Pour lire l'instance la plus récente d'un état (ce que le DSL appelle
`@state`), `urban_workflow.values.find_state_instance(ctx, "NomEtat")`
cherche dans les deux listes. Les champs métier d'une instance
(`extended_datas`) sont **toujours vides** pour l'instant : leur calcul
n'est pas encore cadré.

La validation des appels (`WHEN MontantInferieur(seuil = …)`) se fait
contre la **signature du callable** au chargement du script : un argument
inconnu ou manquant est une erreur de chargement, pas d'exécution.

Bonnes pratiques (détaillées dans [guide-tests.md](guide-tests.md)) :
règles **pures** (pas d'I/O), qui lisent le contexte et retournent un
booléen ; tout effet de bord passe par les actions.

### Règles référencées par script (`AS @script`)

Une règle déclarée `DEFINE RULE R (…) '…' AS @nom;` n'est pas cherchée dans
le `FunctionRegistry` : sa méthode est le script `nom` du
`ScriptRegistry`, chargé à l'initialisation du moteur comme les schémas.

```python
from urban_workflow.scripts import ScriptRegistry

scripts = (
    ScriptRegistry()
    .add_directory("scripts/")                  # un fichier par script (.expr…)
    .add_script("montant_inferieur", "@IncomingEvent.Montant < seuil")
    .add_function("solvable", lambda ctx, client: verifier(client))  # Python
)
config = parse_config(script, rules=rules, schemas=schemas, scripts=scripts)
```

Le langage d'un fichier vient de son extension (`.expr` = langage
`expression`) ; `add_function` enregistre un callable `(ctx, **params)`
dont la signature est contrôlée contre celle de la déclaration. Un langage
supplémentaire s'ajoute avec `register_language` (sous-classe de
`ScriptLanguage` : `name`, `extensions`, `check`, `compile`). Détails :
[guide-regles.md](guide-regles.md).

Les fichiers `.jslt` (langage `jslt`, urban-json) produisent les
**artefacts JSON** (`DEFINE ARTIFACT … USING @script`), données remises aux
actions par `@artifact.Nom`. Un JSON qui ne respecte pas le schéma de
l'artefact lève une `ArtifactError` et interrompt le traitement :
[guide-artefacts.md](guide-artefacts.md).

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
    # Un visiteur neuf par script, avec TOUS les registres : un visiteur
    # sans schemas= accepte les références AS @… sans rien valider, et sans
    # scripts= refuse les règles AS @script et les @artifact.
    return WorkflowConfigVisitor(rules=rules, schemas=schemas, scripts=scripts)

configs = load_directory(WorkflowsConfig(), visitor_factory, "workflows/", "*.wf")
```

Les fichiers `FRAGMENT` sont visités avant les scripts qui les
`INCLUDE` ; chaque script complet devient un document de `configs`.
`parse_directory(chemin, motif)` rend seulement les analyseurs (syntaxe),
sans construire les configurations.

### Contrôle fin

```python
from urban_workflow.dsl import WorkflowScriptParser, WorkflowConfigVisitor

parser = WorkflowScriptParser.parse_string(script_text, filename="x.wf")
parser.check()                 # lève DslSyntaxError si erreurs de syntaxe
parser.includes                # fichiers INCLUDE déclarés
parser.is_fragment             # script FRAGMENT ?
config = parser.visit(WorkflowConfigVisitor(rules=rules, schemas=schemas, scripts=scripts))
```

`parse_config(source, rules=None, filename="", schemas=None, scripts=None)`
fait ces trois étapes d'un coup.

### Lire et réécrire un script (modèle de surface)

Un outil qui édite les workflows (le diagramme du playground, par
exemple) travaille sur le **modèle de surface** : états, transitions et
déclarations sous forme de données, gardes et blocs `EXECUTE`/`STORE` en
texte DSL brut.

```python
from urban_workflow.dsl import SurfaceModel, extract_surface, render_script

model = extract_surface(script_text, filename="x.wf")   # DslSyntaxError, SurfaceError
data = model.to_dict()                                   # JSON-compatible
texte = render_script(SurfaceModel.from_dict(data))      # script canonique
```

`render_script` ne valide rien : repasser le texte à `parse_config`. Les
commentaires `--` ne sont pas conservés, et un script `FRAGMENT` ou à
`INCLUDE` lève `SurfaceError`.

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
`To_State`. `TemplateRegistry(default_template=…)` le remplace (texte
JSLT), ou le supprime avec `None` : une action sans template lève alors
une erreur.

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
2. `processor.output_actions` : une **fabrique** (fonction sans argument)
   qui rend une chaîne neuve à chaque évaluation.

Un maillon hérite d'`OutputAction` et reçoit le maillon suivant en
argument (`child`). Son cycle, pour chaque évaluation :

| Méthode | Appelée | Rôle |
|---|---|---|
| `_prepare_impl(ctx)` | une fois par contexte impacté | choisir ce qu'il y a à faire, le ranger dans `self.items` (rien d'irréversible ici) |
| `_begin_transaction_impl()` | une fois, avant l'exécution | rendre une `Transaction` (par défaut, une transaction vide) |
| `_execute_impl()` | une fois, sous la transaction | faire le travail |

Une `Transaction` implémente `_commit_impl()` et `_rollback_impl()` ; les
transactions de la chaîne sont chaînées entre elles et validées ou annulées
**ensemble** :

```python
import json

from urban_workflow import OutputAction, Transaction
from urban_workflow.outputs import SetPropertiesOutputAction, PushModelOutputAction

class RabbitTransaction(Transaction):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        channel.tx_select()                  # AMQP : messages en attente
    def _commit_impl(self):
        self.channel.tx_commit()
    def _rollback_impl(self):
        self.channel.tx_rollback()

class PushToRabbit(OutputAction):
    def __init__(self, channel, child=None):
        super().__init__(child)
        self.channel = channel
    def _prepare_impl(self, ctx):
        self.items.extend(a for a in ctx.event.actions if a.kind == "$_push")
    def _begin_transaction_impl(self):
        return RabbitTransaction(self.channel)
    def _execute_impl(self):
        for action in self.items:
            self.channel.basic_publish("", "workflow",
                                       json.dumps(action.execute_message))

processor.output_actions = lambda: SetPropertiesOutputAction(   # 1. STORE
    PushToRabbit(channel,                                       # 2. bus
                 PushModelOutputAction(storage)))               # 3. persistance
```

Garder `SetPropertiesOutputAction` en tête : c'est lui qui applique les
`STORE` au workflow ; sans lui, ils sont perdus. Pour un bus sans
transaction, `BusOutputAction(bus, kinds=("$_push",), child=…)` (dans
`urban_workflow.outputs`) pousse vers n'importe quel `OutputBus` (une
méthode `push(action)`) sans écrire de maillon.

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

`engine.evaluate_event(payload, incoming_type=None)` accepte un JSON
(chaîne), un dict, ou un `IncomingEvent` déjà construit, et rend la liste
des `RunContext` impactés (un par workflow touché ; liste vide si aucun).
Propriétés reconnues (CamelCase, héritées du format source) :

| Clé | Rôle |
|---|---|
| `Name` | Nom de l'événement (obligatoire pour router) |
| `Uuid` | Identité de l'événement — **la clé du rejeu sans doublon** |
| `ExternalId` | Identifiant du sujet : regroupe les instances |
| `CreationDate`, `EventDate` | Dates ISO 8601 |
| `DedupKey` | Clé d'idempotence optionnelle fournie par l'émetteur — deux événements portant la même clé ne sont intégrés qu'une fois (prioritaire sur `UNIQUE`) |
| `IntegrationDate` | **Posée par le moteur** (horloge `WorkflowClock`) à l'entrée de `evaluate_event` : date d'insertion dans le système. Une valeur envoyée par l'émetteur est ignorée. Conservée dans l'historique (`Event.integration_date`, colonne SQL `integration_date`) et exposée aux templates (`event.integration_date`, `incoming.integration_date`) |
| *tout le reste* | Données métier (`extended_datas`), visibles des règles, des `MATCHING` et des templates |

Un payload invalide lève `InvalidIncomingEventFormatError`.

### Schémas d'événements (extra `[schemas]`)

Les schémas (JSON Schema **écrits en YAML**) vivent à part des scripts et
se chargent **à l'initialisation du moteur** — fichier, répertoire ou
contenu brut :

```python
from urban_workflow.schemas import SchemaRegistry

schemas = (
    SchemaRegistry()
    .add_directory("schemas/")                 # un .yaml par schéma
    .add_file("schemas/commun.yaml", name="schema_Commun")
    .add_yaml("schema_Ping", "type: object")   # contenu brut
)
config = parse_config(script, rules=rules, schemas=schemas)
```

Le nom d'un schéma (nom de fichier par défaut) est celui que le DSL
référence : `DEFINE EVENT X '…' AS @schema_X;`. Référence inconnue =
erreur positionnée au chargement ; payload non conforme à l'exécution =
`EventSchemaError` (liste complète des violations dans `exc.errors`). Le
socle commun est validé en plus du schéma métier, sauf avec
`SchemaRegistry(include_base=False)`. Sans registre fourni, les références
`AS` sont conservées mais rien n'est validé (mode permissif).

`add_directory(chemin, pattern="*.yaml")` ne lit que les `.yaml` par
défaut : un fichier `.yml` est ignoré sans message (passer
`pattern="*.yml"`). `add_schema(nom, dict)` enregistre un schéma déjà
chargé.

`pip install urban-workflow[schemas]` (PyYAML + jsonschema).

### Verrouillage

Le moteur sérialise les traitements d'un même sujet : la clé est
verrouillée pendant l'évaluation.

```python
engine = WorkflowEngine(
    processor,
    locker=MonVerrouRedis(),                        # défaut : MemoryLocker()
    thread_safe_key=lambda event: event.external_id,  # défaut : l'ExternalId
)
```

`MemoryLocker` ne protège qu'un processus ; un verrou distribué implémente
`LockObject` (`lock(crc)`, `unlock(crc)` sur l'empreinte CRC32 de la clé).
Un verrou non obtenu dans le délai lève `LockFailedError`.

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

`WorkflowFactory(context_factory=MonContexte)` fait créer par le moteur
une sous-classe de `RunContext` (pour donner aux règles Python des
services propres à l'application), et `context_initializer=fonction` est
appelé sur chaque contexte créé.

Le routage d'un événement : les filtres `MATCHING` sélectionnent les
workflows candidats à la **création** ; les instances **existantes** sont
retrouvées par `ExternalId` et traitées avec la configuration de leur
version d'origine. Un même événement peut donc impacter plusieurs
workflows à la fois.

## 8. Les erreurs

Toutes les exceptions héritent de `WorkflowError` et s'importent de
`urban_workflow.exceptions` (les plus courantes aussi de la racine du
paquet).

**Au chargement** (`parse_config`, `load_directory`, `WorkflowConfigVisitor`) —
le script est refusé, avec une position `fichier:ligne:colonne` :

| Exception | Cause |
|---|---|
| `DslSyntaxError` | erreur de syntaxe, du workflow ou d'un script (`expression`, `jslt`) ; `exc.errors` liste chaque erreur positionnée |
| `InvalidMethodReferenceError` | règle non enregistrée, action non déclarée (`DEFINE ACTION`) |
| `InvalidArgumentNameError`, `MissingArgumentNameError` | argument inconnu ou manquant dans un appel de règle ou d'action |
| `InvalidArgumentValueError` | littéral non convertible au type déclaré ; chemin `@` invalide (absent du schéma, `@state` hors d'un état, `@artifact` inconnu ou hors des arguments d'une action) |
| `DuplicatedArgumentNameError` | doublon : argument, paramètre, déclaration (état, événement, constante, artefact), initialiseur, propriété `UNIQUE` |
| `UnknownSchemaError` | `AS @schema` absent du `SchemaRegistry` |
| `UnknownScriptError` | `AS @script` ou `USING @script` absent du `ScriptRegistry` |
| `MissingStateError` | cible de `SWITCH` inexistante, ou branche sans `SWITCH` |

**Au traitement** (`engine.evaluate_event`) — l'événement n'est pas
intégré, la transaction des sorties est annulée, et il peut être rejoué :

| Exception | Cause |
|---|---|
| `InvalidIncomingEventFormatError` | payload illisible (JSON invalide, dates mal formées…) |
| `EventSchemaError` | payload non conforme au socle ou au schéma de l'événement ; `exc.errors` |
| `ArtifactError` | script d'artefact en échec, ou JSON produit non conforme à son schéma ; `exc.errors` |
| `LockFailedError` | verrou du sujet non obtenu |
| `MissingConfigurationError` | workflow ou version introuvable pour une instance existante |

Une règle, elle, ne lève jamais : un script `expression` qui rencontre une
valeur absente ou du mauvais type vaut `NULL`, donc `False`.

## 9. Exemple complet de bout en bout

Un workflow de commandes qui assemble tout ce qui précède : un événement
validé par son schéma, une règle écrite en script, une action dont le
corps est un **artefact JSON** produit par un script `jslt` et validé par
son schéma, et le template du message de cette action. Les fichiers
habituels (`.wf`, `schemas/*.yaml`, `scripts/*.expr|.jslt`,
`templates/*.jslt`) sont ici des chaînes pour que l'exemple s'exécute tel
quel (`pip install urban-workflow[schemas]`).

```python
import json

from urban_workflow import (
    FunctionRegistry, MemoryStorage, Workflow,
    WorkflowEngine, WorkflowFactory, WorkflowProcessor, WorkflowsConfig,
)
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import ArtifactError, EventSchemaError
from urban_workflow.outputs import default_memory_output
from urban_workflow.schemas import SchemaRegistry
from urban_workflow.scripts import ScriptRegistry
from urban_workflow.templating import (
    JsltActionTranslator, MetadataRegistry, TemplateRegistry,
)

# --- Le workflow (d'ordinaire un fichier commandes.wf) -------------------
WORKFLOW = """
NAME Commandes VERSION 1

DEFINE EVENT  CommandeValidee 'commande validée' AS @schema_CommandeValidee;
DEFINE EVENT  Livree          'commande livrée';

DEFINE RULE   GrosMontant (DECIMAL seuil) 'montant au-dessus du seuil'
    AS @gros_montant;

DEFINE ACTION AppelerFacturation (TEXT corps) 'appel du service de facturation';
DEFINE ACTION AlerterCommercial (TEXT client)  'alerte commerciale';

DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;

DEFINE CONST  devise       'EUR' 'devise de facturation';
DEFINE CONST  seuil_alerte 1000  'alerte commerciale au-dessus de ce montant';

INITIALIZE WORKFLOW
    ON EVENT CommandeValidee RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage'
    ON EVENT CommandeValidee
        WHEN GrosMontant(seuil = seuil_alerte)
            EXECUTE AlerterCommercial(client = @IncomingEvent.Client.Nom)
            SWITCH Facturee
        SWITCH Facturee
;

DEFINE STATE Facturee 'facture demandée'
    ON ENTER STATE
        EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)
    ON EVENT Livree
        SWITCH Livree
;

DEFINE STATE Livree 'commande livrée';
"""

# --- Les schémas (d'ordinaire schemas/*.yaml) ----------------------------
schemas = (
    SchemaRegistry()
    .add_yaml("schema_CommandeValidee", """
type: object
required: [Client, Montant]
properties:
  Client:
    type: object
    required: [Nom]
    properties:
      Nom: {type: string}
  Montant: {type: number}
""")
    .add_yaml("schema_RequeteFacture", """
type: object
required: [reference, client, montant, devise]
properties:
  reference: {type: string}
  client:    {type: string}
  montant:   {type: number, exclusiveMinimum: 0}
  devise:    {type: string, enum: [EUR]}
""")
)

# --- Les scripts (d'ordinaire scripts/*.expr et scripts/*.jslt) ----------
scripts = (
    ScriptRegistry()
    .add_script("gros_montant", "@IncomingEvent.Montant > seuil")
    .add_script("requete_facture", """{
    "reference": $.Workflow.ExternalId,
    "client":    $.IncomingEvent.Client.Nom,
    "montant":   $.IncomingEvent.Montant,
    "devise":    $.constants.devise
}""", language="jslt")
)

# --- Le message de chaque action (d'ordinaire templates/*.jslt) ----------
templates = TemplateRegistry().add_template("AppelerFacturation", """{
    "methode": "POST",
    "url":     "https://facturation.exemple/api/factures",
    "corps":   $.action.arguments.corps
}""")
metadatas = MetadataRegistry(default={"canal": "bus-commandes"})

# --- Chargement : toutes les références sont vérifiées ici ---------------
config = parse_config(WORKFLOW, rules=FunctionRegistry("rule"),
                      schemas=schemas, scripts=scripts, filename="commandes.wf")

# --- Assemblage du moteur ------------------------------------------------
storage = MemoryStorage()
processor = WorkflowProcessor(
    WorkflowsConfig().add_document(config), WorkflowFactory(),
    translator=JsltActionTranslator(templates, metadatas),
)
processor.load_existing_workflows_by_external_id = (
    lambda key: storage.get_by(Workflow, key, "external_id")
)
processor.output_actions = default_memory_output(storage)
engine = WorkflowEngine(processor)

# --- Traitement ----------------------------------------------------------
engine.evaluate_event({
    "Name": "CommandeValidee",
    "Uuid": "c0000000-0000-4000-8000-000000000001",
    "ExternalId": "CMD-1",
    "Client": {"Nom": "ACME"},
    "Montant": 1500,
})

commande = storage.get_by(Workflow, "CMD-1", "external_id")[0]
print(commande.current_state)
for action in commande.last_event.actions:
    print(action.name, json.dumps(action.execute_message, ensure_ascii=False))

# --- Les deux erreurs de traitement --------------------------------------
try:   # le payload ne respecte pas schema_CommandeValidee (Client manquant)
    engine.evaluate_event({"Name": "CommandeValidee", "ExternalId": "CMD-2",
                           "Uuid": "c0000000-0000-4000-8000-000000000002",
                           "Montant": 10})
except EventSchemaError as exc:
    print("refusé :", exc.errors)

try:   # l'artefact produit ne respecte pas schema_RequeteFacture (montant 0)
    engine.evaluate_event({"Name": "CommandeValidee", "ExternalId": "CMD-3",
                           "Uuid": "c0000000-0000-4000-8000-000000000003",
                           "Client": {"Nom": "Durand"}, "Montant": 0})
except ArtifactError as exc:
    print("interrompu :", exc.errors)
print(storage.get_by(Workflow, "CMD-3", "external_id"))
```

Sortie (identifiants et dates abrégés) :

```
Facturee
AlerterCommercial {"Header": {"canal": "bus-commandes"}, "Body": {"Uuid": "…", "Name": "AlerterCommercial", "PushedAt": "…", "Arguments": {"client": "ACME"}, "WorkflowId": "…", "EventId": "c0000000-…-000000000001", "From_State": "Tri", "To_State": "Facturee"}}
AppelerFacturation {"Header": {"canal": "bus-commandes"}, "Body": {"methode": "POST", "url": "https://facturation.exemple/api/factures", "corps": {"reference": "CMD-1", "client": "ACME", "montant": 1500, "devise": "EUR"}}}
refusé : ["<racine>: 'Client' is a required property"]
interrompu : ['montant: 0 is less than or equal to the minimum of 0']
[]
```

À retenir :

- **tout est vérifié au chargement** : un nom de schéma, de script, de
  règle ou d'artefact mal orthographié, un chemin `@IncomingEvent.Client.Nom`
  absent du schéma, une erreur de syntaxe dans un script, refusent le
  workflow avant le premier événement ;
- `AlerterCommercial` n'a pas de template : il prend le corps par défaut
  (`Arguments`, `WorkflowId`…) ; `AppelerFacturation` prend le sien, qui
  place l'artefact sous `corps` ;
- CMD-3 n'a laissé **aucune trace** (dernière ligne) : l'artefact invalide
  a interrompu le traitement avant toute écriture.

Ce que le système qui consomme les messages fait du message
`AppelerFacturation` (l'appel HTTP lui-même) est hors du moteur : celui-ci
garantit que le corps est bien formé, puis le pousse dans la chaîne de
sorties (§5).

## 10. Récapitulatif des imports

```python
from urban_workflow import (            # cœur, sans dépendance lourde
    FunctionRegistry, RunContext, Workflow, IncomingEvent, PushedAction,
    WorkflowsConfig, WorkflowFactory, WorkflowProcessor, WorkflowEngine,
    MemoryStorage, MemoryLocker, LockObject, OutputAction, Transaction,
    WorkflowClock, constants,
)
from urban_workflow.dsl import (        # parseur ANTLR (le DSL)
    parse_config, load_directory, parse_directory,
    WorkflowScriptParser, WorkflowConfigVisitor,
)
from urban_workflow.templating import ( # urban-json (templates JSLT)
    JsltActionTranslator, TemplateRegistry, MetadataRegistry,
)
from urban_workflow.outputs import (
    default_memory_output, SetPropertiesOutputAction, PushBusOutputAction,
    PushModelOutputAction, BusOutputAction, OutputBus,
)
from urban_workflow.schemas import SchemaRegistry        # extra [schemas]
from urban_workflow.scripts import ScriptRegistry        # scripts AS/USING @…
from urban_workflow.artifacts import JsltLanguage, produce_artifact
from urban_workflow.values import find_state_instance
from urban_workflow.exceptions import (                  # §8
    WorkflowError, DslSyntaxError, EventSchemaError, ArtifactError,
    UnknownSchemaError, UnknownScriptError,
)
from urban_workflow.storage_sql import SqlWorkflowStorage, sql_output  # extra [sql]
```

`dsl` et `templating` sont des sous-paquets volontairement non réexportés
par la racine : on ne paie leur coût d'import que si on les utilise.
