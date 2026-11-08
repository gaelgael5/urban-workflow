# Guide des artefacts JSON

*Français · [English](en/artifacts-guide.md)*

Un **artefact** est un document JSON **nommé**, produit à la demande à
partir du contexte du workflow, pour être **fourni à autre chose** : le
corps d'un appel HTTP, un message à un autre système, un fichier à
déposer. Produire du JSON n'est pas une fin en soi : l'artefact garantit
qu'une action reçoit une donnée **bien formée**.

```sql
DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;

DEFINE STATE Facturee 'facture demandée'
    ON ENTER STATE
        EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)
;
```

```
// scripts/requete_facture.jslt
{
    "reference": $.Workflow.ExternalId,
    "client":    { "nom": $.IncomingEvent.Client.Nom },
    "lignes":    $.IncomingEvent.Lignes,
    "montant":   $.IncomingEvent.Montant,
    "devise":    $.constants.devise
}
```

## 1. Principe

Un artefact réunit trois choses :

| Élément | Où | Rôle |
|---|---|---|
| le **nom** et le libellé | `DEFINE ARTIFACT` dans le workflow | ce que les actions référencent |
| le **script de production** | `USING @script`, dans le `ScriptRegistry` | construit le JSON à partir du contexte (langage `jslt` en général) |
| le **schéma** (facultatif) | `AS @schema`, dans le `SchemaRegistry` | valide le JSON produit, comme pour les événements et les états |

Comme les règles, le document de workflow ne contient pas de code : il
référence le script, qui vit à côté (voir [guide-regles.md](guide-regles.md)).

## 2. Déclarer un artefact

```sql
DEFINE ARTIFACT Nom 'libellé' [AS @schema] USING @script;
```

- `AS @schema` est facultatif. Sans schéma, le JSON produit n'est pas
  contrôlé.
- `USING @script` est obligatoire.
- Un artefact n'a **pas de paramètres** : son script lit le contexte
  (événement entrant, état, workflow, constantes).
- Les artefacts ont leur propre espace de noms : un artefact peut porter le
  nom d'une règle ou d'une action.

## 3. Consommer un artefact : `@artifact.Nom`

Un artefact se lit par le chemin `@artifact.Nom` dans les **arguments d'une
action** `EXECUTE` :

```sql
EXECUTE AppelerFacturation(corps  = @artifact.RequeteFacture,
                           client = @artifact.RequeteFacture.client.nom)
```

- `@artifact.Nom` donne le JSON complet ; `@artifact.Nom.partie` (ou
  `[0]` pour un élément de liste) n'en donne qu'une partie.
- L'artefact est produit au moment où le message de l'action est construit,
  puis validé contre son schéma. Il part dans la **chaîne de sorties** avec
  l'action, dans `Body.Arguments` du message.
- Il n'est pas disponible ailleurs (arguments d'une règle `WHEN`, scripts) :
  c'est une donnée remise à une action, pas une condition.

## 4. Le langage `jslt`

Les scripts `.jslt` sont des transformations [urban-json](https://github.com/gaelgael5/Jslt)
(JSLT) : le texte du script **est** la forme du JSON produit, les valeurs
venant du document d'entrée par des chemins `$.…`.

### Le document d'entrée

| Chemin | Contenu | Équivalent DSL |
|---|---|---|
| `$.IncomingEvent` | l'événement entrant, format fil (socle + données métier) | `@IncomingEvent` |
| `$.state` | l'instance la plus récente de l'état du bloc qui utilise l'artefact (`Name`, `Uuid`, `CreationDate`, `EventId`, champs métier) ; `null` hors d'un `DEFINE STATE` | `@state` |
| `$.Workflow` | `Uuid`, `ExternalId`, `CurrentState`, `WorkflowName`, `Version` et les données étendues de l'instance | `@Workflow` |
| `$.constants` | les `DEFINE CONST` du workflow | constantes |
| `$.now` | l'heure du moteur (`WorkflowClock`), au format ISO 8601 | `NOW()` |

Un chemin absent donne `null`, sans erreur. C'est le schéma qui décide si
une valeur manquante est acceptable.

### Exemples

```
{
    "commande": $.Workflow.ExternalId,
    "etat":     $.state.Name,
    "depuis":   $.state.CreationDate,
    "total":    $.IncomingEvent.Montant * 1.2,
    "texte":    "Votre commande est livrée",
    "client":   upper($.IncomingEvent.Client.Nom)
}
```

Les fonctions intégrées d'urban-json (`upper`, `lower`, `trim`, `format`,
`round`, `sum`, `uuid`, `sha256`…) sont disponibles. Des fonctions
personnalisées s'ajoutent avec `JsltLanguage(functions=registre)` (voir §6).

Un script peut aussi être écrit dans un autre langage du registre : un
script `expression` produit une valeur (`@IncomingEvent.Montant * 2`), une
fonction Python enregistrée par `add_function` retourne un JSON.

## 5. Contrôles et erreurs

**Au chargement** (`parse_config`), avec des positions `fichier:ligne:colonne` :

- un script ou un schéma inconnu est signalé sur la référence `USING @…`
  ou `AS @…` ;
- une erreur de syntaxe JSLT est positionnée **dans le script**, dès son
  enregistrement (`requete_facture.jslt:3:12`) ;
- `@artifact.Inconnu` est refusé, ainsi que `@artifact.X.partie` quand
  `partie` n'existe pas dans le schéma de l'artefact ;
- `@artifact.…` est refusé hors des arguments d'une action ;
- un artefact déclaré deux fois est refusé.

**Au traitement**, une `ArtifactError` est levée si :

- le script échoue (fonction inconnue, opération impossible) ;
- le JSON produit ne respecte pas le schéma. Le message liste les
  violations (`montant: 0 is less than or equal to the minimum of 0`), et
  `exc.errors` les donne une par une.

L'erreur **interrompt le traitement de l'événement**, et la transaction des
sorties est annulée. C'est voulu, et c'est l'inverse d'une règle (qui vaut
`False` plutôt que d'échouer) : une donnée mal formée ne doit pas partir en
silence vers le système qui l'attend.

**Sans registre** : si `parse_config` ne reçoit pas de `scripts`, les
déclarations sont gardées (références non résolues), mais un
`@artifact.X` est refusé, faute de quoi produire l'artefact. Sans
`schemas`, la référence `AS @…` est gardée et rien n'est validé.

## 6. Dans le code

```python
from urban_workflow.dsl import parse_config
from urban_workflow.schemas import SchemaRegistry
from urban_workflow.scripts import ScriptRegistry

scripts = ScriptRegistry().add_directory("scripts/")   # .jslt, .expr…
schemas = SchemaRegistry().add_directory("schemas/")
config = parse_config(workflow_text, schemas=schemas, scripts=scripts)
```

Le langage `jslt` est fourni par défaut (`urban-json` est déjà une
dépendance du moteur). Pour lui donner des fonctions personnalisées :

```python
from urban_json import default_registry
from urban_workflow.artifacts import JsltLanguage
from urban_workflow.dsl.expressions import ExpressionLanguage
from urban_workflow.scripts import PythonLanguage, ScriptRegistry

functions = default_registry.copy()
functions.register("iban_masque", lambda ctx, iban: "****" + iban[-4:])
scripts = ScriptRegistry(languages=[
    ExpressionLanguage(), PythonLanguage(), JsltLanguage(functions=functions),
])
```

Produire un artefact hors d'une action (aperçu, test, code hôte), avec le
même script, le même document et la même validation :

```python
from urban_workflow.artifacts import produce_artifact

json_value = produce_artifact(
    config, "RequeteFacture", scripts, run_ctx,
    state_name="Facturee", constants={"devise": "EUR"},
)
```

Le `TemplateRegistry` des messages d'action (§4 de
[guide-integration.md](guide-integration.md)) est un mécanisme **séparé** :
il met en forme l'enveloppe du message, alors que l'artefact est une donnée
passée en argument.

## 7. Dans le playground

- Dans l'éditeur, `USING @` propose les scripts, `AS @` les schémas, et
  `@artifact.` les artefacts avec leurs parties connues par le schéma.
- La vue **Scripts** édite les scripts `jslt`. Elle propose les chemins
  `$.…` du document d'entrée et les fonctions d'urban-json, et souligne les
  erreurs de syntaxe dans le script.
- **Aperçu** : sous l'éditeur, « Produire le JSON » applique le script et
  le schéma à un événement d'exemple (le premier de la simulation, que l'on
  peut modifier), dans l'état choisi. Par défaut, c'est l'état où
  l'artefact est utilisé.
- La simulation montre l'artefact dans le message de l'action. Une
  violation de schéma apparaît en erreur sur l'événement concerné.
- L'exemple « Artefacts JSON » montre deux artefacts, l'un validé par un
  schéma et l'autre sans, avec une commande qui respecte le schéma et une
  autre qui ne le respecte pas.
