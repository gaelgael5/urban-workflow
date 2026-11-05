# Guide du langage — créer un workflow

Un workflow urban-workflow est une **machine à états** déclarée dans un
fichier texte, dans un langage dédié de style SQL. Ce document est la
référence complète du langage : chaque construction, sa syntaxe, sa
sémantique et ses cas d'usage.

> L'intégration côté Python (moteur, règles métier, templates de sortie)
> est traitée dans [guide-integration.md](guide-integration.md) ; l'écriture
> des règles et les tests dans [guide-tests.md](guide-tests.md).

## 1. Vue d'ensemble

Un script décrit :

1. **l'identité** du workflow (nom, version, description) ;
2. **le routage** : quels événements entrants le concernent (`MATCHING`) ;
3. **le référentiel** : les événements, règles, actions et constantes
   utilisés (`DEFINE …`) — tout est déclaré avant d'être utilisé, et le
   parseur valide chaque usage à la construction ;
4. **la création** : quel événement crée une instance de workflow pour
   traiter un nouveau sujet (`INITIALIZE WORKFLOW`) ;
5. **les états** et leurs transitions (`DEFINE STATE … ON EVENT … SWITCH`).

Squelette complet :

```sql
NAME MonWorkflow VERSION 1
CONCURENCY 1
DESCRIPTION 'ce que fait ce workflow'
MATCHING (Type = 'achat')

DEFINE EVENT  …;        -- référentiel : au moins une déclaration requise
DEFINE RULE   …;
DEFINE ACTION …;
DEFINE CONST  …;

INITIALIZE WORKFLOW     -- création des instances
    ON EVENT … SWITCH …

DEFINE STATE …          -- un bloc par état, terminé par ;
;
```

L'ordre des sections est imposé par la grammaire : en-tête, déclarations,
`INITIALIZE WORKFLOW`, puis les états.

**Commentaires** : `-- jusqu'à la fin de ligne` et `/* bloc */`.
**Chaînes** : entre quotes simples, `''` échappe une quote
(`'l''événement'`).

## 2. L'en-tête

```sql
NAME ValidationAchat VERSION 2
CONCURENCY 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat' Pays = 'France')
```

| Clause | Rôle | Défaut |
|---|---|---|
| `NAME nom` | Identifiant du workflow (obligatoire) | — |
| `VERSION n` | Version de cette configuration | `1` |
| `CONCURENCY n` | Nombre maximal d'instances simultanées pour un même sujet (même `ExternalId`) | `1` |
| `DESCRIPTION '…'` | Libellé lisible | vide |
| `MATCHING (clé = 'valeur' …)` | Filtre de routage : l'événement entrant doit porter **toutes** ces paires dans ses données pour que ce workflow soit candidat | aucun filtre |

### Versionner un workflow

Plusieurs scripts peuvent porter le même `NAME` avec des `VERSION`
différentes et être chargés ensemble. Une instance **créée** avec la
version 1 continue sa vie sur la configuration 1 ; les **nouvelles**
instances peuvent être restreintes à une version donnée côté code
(`WorkflowsConfig.set_version_selector`). C'est le mécanisme de migration
sans interruption : on déploie la v2, on fige les créations sur la v2, les
dossiers v1 en cours se terminent sur la v1.

### Router par `MATCHING`

Plusieurs workflows différents peuvent être chargés dans le même moteur.
À l'arrivée d'un événement, seuls ceux dont le filtre `MATCHING` est
satisfait sont candidats à la création :

```sql
-- fichier achats.wf
NAME CircuitAchats
MATCHING (Type = 'achat')
…

-- fichier conges.wf
NAME CircuitConges
MATCHING (Type = 'conge')
…
```

Un événement `{ "Type": "achat", … }` ne crée que des instances de
`CircuitAchats`.

## 3. Le référentiel (`DEFINE`)

Chaque déclaration se termine par `;`. **Au moins une déclaration est
requise** par script. Toute utilisation d'un nom non déclaré, tout
argument inconnu ou manquant, tout doublon, est une erreur **positionnée**
(`fichier:ligne:colonne`) levée au chargement — jamais à l'exécution.

### Événements

```sql
DEFINE EVENT DemandeSoumise 'une demande est déposée'
    AS @schema_DemandeSoumise UNIQUE (ExternalId, Montant);
```

Déclare un événement métier que le workflow accepte. Un événement reçu
mais non déclaré est ignoré par ce workflow. Deux clauses optionnelles
(extensions urban-workflow) :

- **`AS @nom`** — référence un **JSON Schema écrit en YAML**, enregistré
  à part et chargé à l'initialisation du moteur (voir
  [guide-integration.md](guide-integration.md) §6) ; chaque événement
  entrant de ce nom est alors validé contre le socle commun (`Name`,
  `Uuid`, `ExternalId`, `CreationDate`, `EventDate`, `DedupKey`,
  `IntegrationDate` — cette dernière posée par le moteur) **et**
  contre ce schéma — payload non conforme = `EventSchemaError` ;
- **`UNIQUE (Prop, …)`** — anti-doublon fonctionnel : le moteur hache la
  concaténation de ces propriétés du payload (SHA-256) et **ignore** tout
  événement dont l'empreinte existe déjà dans l'historique du workflow
  (même mécanique silencieuse que l'anti-rejeu par `Uuid`). Si l'émetteur
  fournit la propriété réservée **`DedupKey`** dans le payload (clé
  d'idempotence), elle est **prioritaire** sur `UNIQUE`.

### Règles

```sql
DEFINE RULE MontantInferieur (DECIMAL seuil) 'le montant est sous le seuil';
```

Une règle est un **prédicat métier** utilisé dans les conditions `WHEN`.
Sa signature (`TEXT`, `INTEGER`, `DECIMAL`) type les arguments : un
littéral `'500'` passé à un paramètre `DECIMAL` arrive en `float` côté
Python. L'implémentation est un callable Python enregistré sous le même
nom (voir [guide-integration.md](guide-integration.md) §2).

### Actions

```sql
DEFINE ACTION NotifierValideur (TEXT niveau) 'demande d''approbation';
```

Une action est un **message poussé vers l'extérieur** (bus, file, API…)
quand le workflow la déclenche. Contrairement aux règles, elle n'a pas
d'implémentation Python : sa matérialisation en JSON passe par un template
(voir [guide-integration.md](guide-integration.md) §4).

Règles et actions partagent le même espace de noms : déclarer `RULE X`
puis `ACTION X` est une erreur.

### Constantes

```sql
DEFINE CONST seuil_auto 500          'seuil d''approbation automatique';
DEFINE CONST service    'achats'     'nom du service';
DEFINE CONST relance    2 DAY        'délai de relance';
```

Une constante se référence ensuite **par son nom nu** dans un argument :
`MontantInferieur(seuil = seuil_auto)`. Les valeurs possibles : chaîne,
nombre, délai (`n MINUTE|HOUR|DAY`, converti en minutes), identifiant.

## 4. Les arguments d'appel

Dans `regle(arg = …)` comme dans `action(arg = …)`, quatre formes de
valeur :

| Forme | Exemple | Sémantique |
|---|---|---|
| Littéral | `motif = 'dossier incomplet'` | Valeur fixe, convertie au type déclaré du paramètre |
| Chemin `@` | `cible = @Workflow.ExternalId` | **Référence paresseuse** résolue à l'exécution contre le contexte |
| Nom nu | `seuil = seuil_auto` | Constante `DEFINE CONST` si elle existe, sinon littéral texte |
| Chemin `$` | `montant = $.Montant` | **JSONPath** dans le document de l'événement entrant (extension urban-workflow, voir ci-dessous) |

### Les chemins `@`

Un chemin navigue dans le contexte d'exécution, segment par segment :

- `@Workflow.…` — l'instance : `Uuid`, `ExternalId`, `CurrentState`,
  `WorkflowName`, `Version`, et toute clé de ses données étendues
  (ce que `STORE` y a écrit, plus les données de l'événement créateur) ;
- `@IncomingEvent.…` — l'événement entrant : `Name`, `Uuid`,
  `ExternalId`, `EventDate`, et toute clé de son payload
  (`@IncomingEvent.Montant`) ;
- `@Event.…` — l'événement en cours d'intégration dans l'historique :
  `Name`, `FromState`, `ToState`, et les données copiées de l'entrant.

Les chemins acceptent le CamelCase du DSL même si les attributs Python
sont en snake_case (`@Workflow.ExternalId` → `workflow.external_id`), et
retombent sur les données étendues quand le segment n'est pas un attribut.

### Les chemins `$` (JSONPath sur l'événement)

`$` désigne le **document de l'événement entrant**, celui que valident
les schémas : socle commun (`Name`, `Uuid`, `ExternalId`, `CreationDate`,
`EventDate`, `DedupKey`, `IntegrationDate`) + données métier du payload.
On y écrit donc les mêmes noms que dans le YAML du schéma :

```
ON EVENT DemandeSoumise
    WHEN MontantInferieur(seuil = $.Montant)
     AND PaysAutorise(pays = $.Client.Pays)
     AND QuantiteValide(qte = $.Lignes[0].Qte)
    SWITCH EnValidation
```

- Segments : `.Prop`, index de liste `[n]`, et `['nom']` pour un nom qui
  n'est pas un identifiant (ou qui est un mot-clé). `$` seul passe le
  document entier. Pas de filtres ni de jokers : une règle reçoit
  **une** valeur.
- La valeur garde son type JSON (pas de conversion vers le type déclaré,
  comme pour `@`). Un chemin absent donne `None` : un champ facultatif
  manquant est un cas métier normal, que la règle tranche.
- **Vérifié au chargement** : dans `ON EVENT X …`, si X est déclaré avec
  un schéma (`AS @…`) et que le moteur reçoit le registre de schémas, un
  chemin inconnu (`$.Montnt`) est une erreur positionnée
  (`fichier:ligne:col`). Le contrôle s'arrête sans erreur là où le schéma
  ne permet pas de trancher (`$ref`, `allOf`/`anyOf`/`oneOf`,
  `patternProperties`, `additionalProperties` décrit par un schéma).
- Dans le playground, taper `$.` propose les propriétés de l'événement du
  bloc `ON EVENT` courant (le socle seul hors d'un tel bloc).

## 5. Créer une instance pour traiter un sujet (`INITIALIZE WORKFLOW`)

C'est **la** réponse à « un nouveau sujet arrive, ouvre un dossier » :

```sql
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise
        WHEN EstComplet(champs = 'Montant')
        SWITCH EnValidation
```

À l'arrivée d'un événement `DemandeSoumise` qui passe le filtre
`MATCHING` et dont la condition `WHEN` est vraie, une instance est créée,
identifiée par l'`ExternalId` de l'événement (le numéro du dossier, du
client, de la commande…), et placée dans l'état `SWITCH`. Les données du
payload sont copiées dans les données étendues de l'instance.

Points de sémantique :

- **un seul chemin d'initialisation par nom d'événement** — pour aiguiller
  vers des états différents selon des conditions, utiliser le motif
  « état d'aiguillage + `RECURSIVE` » ci-dessous ;
- `CONCURENCY` borne le nombre d'instances simultanées du même workflow
  pour un même `ExternalId` ; au-delà, l'événement n'en crée plus ;
- un événement déjà intégré (même `Uuid`) ne crée jamais de doublon
  (rejeu sans effet).

### `RECURSIVE` : enchaîner immédiatement une transition

Sans `RECURSIVE`, l'instance est créée dans l'état cible et attend
l'événement suivant. Avec `RECURSIVE`, **le même événement est aussitôt
réévalué** dans l'état cible, ce qui permet de créer *et* d'aiguiller d'un
seul mouvement :

```sql
INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            SWITCH Incomplete
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        SWITCH EnValidation
;
```

Ici l'instance naît dans `Tri`, et la demande est immédiatement redirigée
vers `Incomplete`, `Approuvee` ou `EnValidation` selon les règles.

## 6. États et transitions (`SWITCH`)

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'

    ON EVENT ValidationAccordee
        SWITCH Approuvee

    ON EVENT ValidationRefusee
        EXECUTE NotifierDemandeur(motif = @IncomingEvent.Motif)
        SWITCH Rejetee
;
```

Un bloc `ON EVENT nom` liste des **branches** (`switch_state`). À
l'arrivée de l'événement, les branches sont évaluées **dans l'ordre** ; la
**première** dont le `WHEN` est vrai (ou qui n'a pas de `WHEN`) est
appliquée, les suivantes sont ignorées. Une branche peut :

- changer d'état (`SWITCH cible`) — la cible doit exister, c'est vérifié
  au chargement ;
- exécuter des actions avant de changer d'état (`EXECUTE … SWITCH …`) ;
- exécuter des actions **sans changer d'état** (branche sans `SWITCH`).

La branche sans `WHEN` en dernière position sert de **cas par défaut**.

### Les conditions `WHEN`

Une condition combine des appels de règles avec `NOT`, `AND`, `OR` et des
parenthèses :

```sql
WHEN (EstComplet(champs = 'Montant') AND NOT MontantInferieur(seuil = seuil_auto))
     OR EstUrgent(niveau = @IncomingEvent.Priorite)
```

Chaque évaluation de règle est tracée dans le journal fonctionnel du
contexte (`IsMajor(agemin=18) -> True`), ce qui rend les décisions du
moteur auditables.

### Cas d'usage : circuit de validation

Le motif complet « soumission → validation → approbation/rejet, avec
dossier incomplet et relance » :

```sql
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
```

## 7. Déclencher des actions

### `EXECUTE` — pousser un message

```sql
EXECUTE NotifierValideur(niveau = 'standard', dossier = @Workflow.ExternalId)
```

Produit une action de kind `$_push`, matérialisée en message JSON (via son
template) et poussée sur le bus de sortie. Plusieurs appels peuvent se
suivre dans la même branche.

### Kind personnalisé

```sql
audit NotifierValideur(niveau = 'trace')
```

En remplaçant le mot-clé `EXECUTE` par un identifiant, l'action est
produite avec ce kind (`audit` ici) au lieu de `$_push` — utile pour
router différemment certaines actions dans la chaîne de sorties.

### `STORE` — écrire dans les données du workflow

```sql
STORE (Statut = 'approuvee' Etape = 'fin')
```

Produit des actions de kind `$_update` qui écrivent les paires dans les
**données étendues de l'instance**. Ces valeurs sont ensuite lisibles par
les chemins `@Workflow.Statut` et par le code hôte.

### `ON ENTER STATE` / `ON EXIT STATE`

Des actions attachées à **l'entrée** ou **la sortie** d'un état, quelle
que soit la transition qui y mène :

```sql
DEFINE STATE Approuvee 'demande approuvée'
    ON ENTER STATE
        WHEN NotifActive(canal = 'mail')
            EXECUTE NotifierDemandeur(motif = 'approbation', dossier = @Workflow.ExternalId)
    ON EXIT STATE
        EXECUTE Auditer(etape = 'sortie-approuvee')
    ON ENTER AND EXIT STATE
        EXECUTE Tracer(etat = 'Approuvee')
;
```

Chaque bloc accepte un `WHEN` optionnel. Lors d'une transition, l'ordre de
collecte est : actions de l'événement, actions de la transition, `ON EXIT`
de l'état quitté, `ON ENTER` de l'état atteint.

### `WAITING … BEFORE` — différer une action

```sql
ON ENTER STATE
    WAITING 10 MINUTE BEFORE
    EXECUTE NotifierValideur(niveau = 'rappel', dossier = @Workflow.ExternalId)
```

L'action est poussée **encapsulée dans un message de rappel**
(`$_reminder`) portant le délai en minutes : c'est l'infrastructure hôte
(bus de rappel différé) qui la rejouera à l'échéance. Unités : `MINUTE`,
`HOUR`, `DAY`.

## 8. Expiration d'un état (`EXPIRE AFTER`)

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        SWITCH Approuvee
    EXPIRE AFTER 3 DAY
        SWITCH Expiree
;
```

`EXPIRE AFTER` met en place le cycle complet d'expiration :

1. **à l'entrée** dans l'état, un rappel différé `__expired` (3 jours ici)
   est poussé sur le bus de rappel ;
2. **à la sortie** de l'état par une autre transition, une action
   d'annulation du rappel (`__cancelReminderAction`) est poussée ;
3. quand le rappel revient sous forme d'événement **`__expired`** (porté
   par l'infrastructure, avec `WorkflowId` et `CurrentState`), la
   transition d'expiration s'applique — **seulement si l'état n'a pas
   changé** entre-temps : un rappel périmé est ignoré.

Un `WHEN` supplémentaire sur la branche d'expiration se combine (ET) avec
cette garde automatique.

## 9. Fragments réutilisables (`FRAGMENT` / `INCLUDE`)

Un référentiel partagé entre plusieurs workflows (mêmes événements, mêmes
règles, mêmes constantes) se déclare une fois dans un **fragment** :

```sql
-- referentiel.wf
FRAGMENT NAME referentiel
DESCRIPTION 'déclarations communes du domaine achats'
DEFINE EVENT DemandeSoumise 'une demande est déposée';
DEFINE RULE  EstComplet (TEXT champs) 'les champs requis sont présents';
DEFINE CONST seuil_auto 500 'seuil d''approbation automatique';
```

et s'importe dans chaque script complet :

```sql
-- validation.wf
INCLUDE 'referentiel.wf'
NAME ValidationAchat VERSION 1
DEFINE ACTION NotifierValideur (TEXT niveau) 'demande d''approbation';
…
```

Au chargement d'un répertoire, les fragments sont résolus par nom de
fichier et visités avant le script qui les inclut : leurs déclarations
sont disponibles comme si elles étaient locales.

## 10. Les erreurs du parseur

Le chargement échoue tôt, avec des messages positionnés :

| Erreur | Exemple de cause |
|---|---|
| `DslSyntaxError` | Syntaxe invalide, `;` manquant — chaque erreur porte fichier, ligne, colonne |
| `InvalidMethodReferenceError` | `EXECUTE Inconnue(…)` sans `DEFINE ACTION`, ou `WHEN RegleNonEnregistree(…)` |
| `InvalidArgumentNameError` | Argument absent de la signature déclarée |
| `MissingArgumentNameError` | Paramètre déclaré non fourni |
| `DuplicatedArgumentNameError` | Doublon : déclaration, paramètre, argument, état, événement d'un état |
| `InvalidArgumentValueError` | `'abc'` passé à un paramètre `INTEGER` |
| `MissingStateError` | `SWITCH EtatInexistant` |

Toutes héritent de `WorkflowError`.

## 11. Aide-mémoire

```sql
NAME nom VERSION n                        -- identité
CONCURENCY n                              -- instances max par sujet
DESCRIPTION 'libellé'
MATCHING (K = 'v' …)                      -- routage des événements

DEFINE EVENT  Nom 'libellé' [AS @schema] [UNIQUE (Prop, …)];
DEFINE RULE   Nom (TYPE arg, …) 'libellé';     -- TYPE : TEXT|INTEGER|DECIMAL
DEFINE ACTION Nom (TYPE arg, …) 'libellé';
DEFINE CONST  nom valeur 'libellé';            -- valeur : 'txt' | 42 | n DAY

INITIALIZE WORKFLOW
    ON EVENT Nom [WHEN cond] [RECURSIVE] SWITCH Etat

DEFINE STATE Etat 'libellé'
    ON ENTER STATE | ON EXIT STATE | ON ENTER AND EXIT STATE
        [WHEN cond] [WAITING n UNITE BEFORE] actions
    ON EVENT Nom
        [WHEN cond] [actions] [SWITCH Cible]   -- branches dans l'ordre, la 1re vraie gagne
    EXPIRE AFTER n UNITE
        [WHEN cond] [actions] SWITCH Cible
;

-- actions :
EXECUTE Action(arg = 'litteral', arg2 = @Chemin.Compose, arg3 = constante)
monkind Action(…)                         -- kind personnalisé
STORE (Cle = 'valeur' …)                  -- écrit dans @Workflow.Cle

-- conditions :
WHEN Regle(a = 1) AND (NOT Autre(b = 'x') OR Tierce(c = @IncomingEvent.K))
```
