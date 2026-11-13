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

DEFINE EVENT  …;        -- référentiel (facultatif : tout peut venir d'un INCLUDE)
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
  (même mécanique silencieuse que l'anti-rejeu par `Uuid`).

#### Comment le moteur choisit la clé de dédoublonnage

Le dédoublonnage est **toujours actif** : à défaut de clé explicite, le
moteur se replie sur le socle de l'événement. Première règle qui
s'applique, de la plus explicite au repli :

| # | Clé utilisée | Quand |
|---|---|---|
| 1 | `DedupKey` | l'émetteur fournit cette propriété réservée (clé d'idempotence) |
| 2 | les propriétés `UNIQUE (…)` | paramétrage déclaré sur `DEFINE EVENT` |
| 3 | `Uuid` | ni l'un ni l'autre, mais le payload porte un `Uuid` non nul |
| 4 | `Name` + `EventDate` (+ `ExternalId` s'il est renseigné) | ni l'un ni l'autre, et pas d'`Uuid` dans le payload |
| — | *aucune* (rien n'est dédoublonné) | pas d'`Uuid` **et** pas d'`EventDate` |

Le cas 4 est la **signature fonctionnelle** de l'événement : même type,
même date fonctionnelle, même dossier = même événement. L'`ExternalId`
entre dans l'empreinte quand il est renseigné, pour que deux dossiers
différents ne se dédoublonnent pas l'un contre l'autre.

Le dernier cas est volontaire : `Name` (+ `ExternalId`) seuls
rejetteraient *tout* événement ultérieur du même type sur le même
dossier. Un dédoublonnage trop large perd des événements en silence,
alors que son absence laisse au pire passer un doublon — un événement
sans `Uuid` ni `EventDate` a donc besoin d'un `UNIQUE` ou d'un `DedupKey`
pour être dédoublonné.

Un appelant qui construit lui-même un `IncomingEvent` au lieu de passer
un payload met `uuid_from_payload=True` pour que son `Uuid` serve de clé
(cas 3) : sans ce drapeau, l'`Uuid` généré par défaut serait indiscernable
d'un `Uuid` porteur de sens.

**Portée : le dossier, pas le système.** L'empreinte est comparée à
l'historique des workflows du **même `ExternalId`** — jamais à toute la
base. Deux événements portant le même `DedupKey` mais deux `ExternalId`
différents sont donc intégrés tous les deux : `DedupKey` est une clé
d'idempotence *par dossier*, pas un identifiant global. Même règle pour
`UNIQUE`.

**Règles communes aux quatre cas :**

- le rejet est **silencieux** — l'événement est ignoré, aucune exception,
  aucun workflow impacté (`evaluate_event` rend une liste vide) ;
- l'empreinte retenue est conservée dans l'historique
  (`Event.dedup_hash`, colonne SQL `workflow_events.dedup_hash`), ce qui
  rend le contrôle idempotent au rejeu ;
- une propriété **absente compte comme vide** dans le hash : deux
  événements qui ne diffèrent que par une propriété hors clé ont la même
  empreinte ;
- le contrôle ne s'applique qu'aux événements que la configuration
  traiterait vraiment (déclarés par `DEFINE EVENT`) ;
- il vaut pour les **deux chemins** : les workflows existants et la
  création d'une nouvelle instance ;
- l'anti-rejeu par `Uuid` (même `Uuid` déjà intégré) reste actif en plus,
  indépendamment de la clé retenue.

### Règles

```sql
DEFINE RULE MontantInferieur (DECIMAL seuil) 'le montant est sous le seuil';
```

Une règle est un **prédicat métier** utilisé dans les conditions `WHEN`.
Sa signature (`TEXT`, `INTEGER`, `DECIMAL`) type les arguments : un
littéral `'500'` passé à un paramètre `DECIMAL` arrive en `float` côté
Python. L'implémentation est soit un callable Python enregistré sous le
même nom (voir [guide-integration.md](guide-integration.md) §2), soit un
**script référencé** (ci-dessous).

#### Règles implémentées par un script (`AS @script`)

Extension urban-workflow : le document de workflow ne porte pas de code.
Une règle **référence** sa méthode, écrite à côté et chargée à
l'initialisation du moteur dans un `ScriptRegistry`, comme les schémas :

```sql
DEFINE RULE MontantInferieur (DECIMAL seuil) 'le montant est sous le seuil'
    AS @montant_inferieur;
```

```sql
-- montant_inferieur.expr
@IncomingEvent.Montant < seuil
```

La règle s'appelle exactement comme une règle de code
(`WHEN MontantInferieur(seuil = seuil_auto)`) ; le script utilise les
paramètres typés de la déclaration. Le langage du script est choisi au
chargement : langage `expression` (fichiers `.expr` : comparaisons, `IN`,
`IS NULL`, calcul, `NOW()`, `DAYS_BETWEEN`…), fonction Python, ou tout
langage enregistré. Une règle a un script OU une fonction de code sous son
nom, jamais les deux. Un nom de script inconnu est refusé au chargement.

Référence complète (langages, langage `expression`, sémantique `NULL`,
contrôles) : [guide-regles.md](guide-regles.md).

### Actions

```sql
DEFINE ACTION NotifierValideur (TEXT niveau) 'demande d''approbation';
DEFINE ACTION Archiver (TEXT dossier) 'archivage' AS @archiver;
```

Une action est un **message poussé vers l'extérieur** (bus, file, API…)
quand le workflow la déclenche. Contrairement aux règles, elle n'a pas
d'implémentation Python : sa matérialisation en JSON passe par un template
(voir [guide-integration.md](guide-integration.md) §4).

Extension urban-workflow : une action peut aussi référencer une méthode
(`AS @script`), pour la même raison que les règles. La référence est
vérifiée au chargement ; l'exécution des méthodes d'action reste à cadrer
(aujourd'hui sans effet).

Règles et actions partagent le même espace de noms : déclarer `RULE X`
puis `ACTION X` est une erreur.

### Artefacts

```sql
DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;
```

Extension urban-workflow : un artefact est un document JSON **nommé**,
produit par un script (`USING @…`, en général `jslt`) et validé par un
schéma facultatif (`AS @…`). Il fournit une donnée bien formée à une
action : `EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture)`.
Pas de paramètres : le script lit le contexte. Détails :
[guide-artefacts.md](guide-artefacts.md).

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

Dans `regle(arg = …)` comme dans `action(arg = …)`, trois formes de
valeur :

| Forme | Exemple | Sémantique |
|---|---|---|
| Littéral | `motif = 'dossier incomplet'` | Valeur fixe, convertie au type déclaré du paramètre |
| Chemin `@` | `cible = @Workflow.ExternalId`, `montant = @IncomingEvent.Montant` | **Référence paresseuse** résolue à l'exécution contre le contexte |
| Nom nu | `seuil = seuil_auto` | Constante `DEFINE CONST` si elle existe, sinon littéral texte |

### Les chemins `@`

Un chemin navigue dans le contexte d'exécution, segment par segment :

- `@Workflow.…` — l'instance : `Uuid`, `ExternalId`, `CurrentState`,
  `WorkflowName`, `Version`, et toute clé de ses données étendues
  (ce que `STORE` y a écrit, plus les données de l'événement créateur) ;
- `@IncomingEvent.…` — l'**événement entrant** (voir ci-dessous) ;
- `@state.…` — l'**instance de l'état courant** (voir ci-dessous) ;
- `@artifact.Nom[.partie]` — un **artefact JSON** produit à la demande,
  seulement dans les arguments d'une action
  ([guide-artefacts.md](guide-artefacts.md)) ;
- `@Event.…` — ancien chemin vers l'événement en cours d'historisation,
  conservé pour les scripts existants mais plus proposé : les états de
  départ et d'arrivée ne sont pas des propriétés de l'événement (un même
  événement peut être traité en parallèle par plusieurs workflows) ; c'est
  l'état qui référence l'événement (`@state.EventId`).

Les chemins acceptent le CamelCase du DSL même si les attributs Python
sont en snake_case (`@Workflow.ExternalId` → `workflow.external_id`), et
retombent sur les données étendues quand le segment n'est pas un attribut.

### `@IncomingEvent` et `@state` : des documents JSON

Ces deux racines désignent des **documents** — les mêmes objets que dans
les vues Événements et États du playground et que dans le YAML des
schémas — et acceptent, en plus des `.Prop`, les index de liste `[n]` et
les clés `['nom']` (nom qui n'est pas un identifiant, ou mot-clé) :

```
DEFINE STATE Tri 'aiguillage' AS @schema_Tri
    ON EVENT DemandeSoumise
        WHEN MontantInferieur(seuil = @IncomingEvent.Montant)
         AND PaysAutorise(pays = @IncomingEvent.Client.Pays)
         AND QuantiteValide(qte = @IncomingEvent.Lignes[0].Qte)
        SWITCH EnValidation
```

- **`@IncomingEvent`** : le document que valident les schémas
  d'événements — socle (`Name`, `Uuid`, `ExternalId`, `CreationDate`,
  `EventDate`, `DedupKey`, `IntegrationDate` posée par le moteur) +
  données métier du payload. Il ne porte rien de propre à un workflow.
- **`@state`** : l'instance de l'état du bloc `DEFINE STATE` où l'on écrit
  — socle `Name`, `Uuid`, `CreationDate` (entrée dans l'état), `EventId`
  (l'événement qui a créé l'instance) + champs du schéma de l'état
  (déclarés et contrôlés, mais **toujours absents pour l'instant** : leur
  calcul n'est pas encore cadré, ils valent donc `NULL`). Dans
  `ON EVENT`, c'est l'état courant ; dans `ON ENTER`, l'instance qui vient
  d'être créée. **Indisponible dans `INITIALIZE WORKFLOW`** (aucun état
  n'existe encore) : erreur positionnée.
- `@IncomingEvent` (ou `@state`) seul passe le document entier. Pas de
  filtres ni de jokers : une règle reçoit **une** valeur. La valeur garde
  son type JSON (pas de conversion vers le type déclaré). Un chemin absent
  donne `None` : un champ facultatif manquant est un cas métier normal.
- Les segments `[n]` / `['nom']` ne sont acceptés que sur ces deux racines.
- **Vérifié au chargement** : si l'objet désigné a un schéma (`AS @…`) et
  que le moteur reçoit le registre de schémas, un chemin inconnu
  (`@IncomingEvent.Montnt`, `@state.Decisoin`) est une erreur positionnée
  (`fichier:ligne:col`). Le contrôle s'arrête sans erreur là où le schéma
  ne permet pas de trancher (`$ref`, `allOf`/`anyOf`/`oneOf`,
  `patternProperties`, `additionalProperties` décrit par un schéma).
- Dans le playground, `@IncomingEvent.` propose les propriétés de
  l'événement du bloc `ON EVENT` courant, `@state.` celles de l'état du
  bloc `DEFINE STATE` courant — champs métier d'abord, socle ensuite.

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
vers `Incomplete`, `Approuvee` ou `EnValidation` selon les règles (deux
instances d'état : `Tri`, puis la cible).

**Switch viable.** Tout switch (initialisation ou transition, avec ou
sans `RECURSIVE`) n'est retenu que si l'état cible **offre ensuite une
route** pour l'événement courant : une branche qui passe (`WHEN` vrai ou
branche sans `WHEN`), ou aucun `ON EVENT` pour cet événement. Si `Tri` gère
`DemandeSoumise` mais qu'aucune de ses branches ne passe, tout se passe
**comme si ce switch n'avait pas été rencontré** : pas d'instance `Tri`,
aucune action, on reste dans l'état courant (ou pas de workflow créé, pour
un initialiseur) et la branche suivante est essayée ; la raison est tracée
dans le journal fonctionnel. Le moteur .NET d'origine laissait au
contraire l'instance bloquée dans `Tri`, sans le signaler.

La route trouvée n'est **suivie** qu'avec `RECURSIVE` ; sans, elle sert
seulement au contrôle. Le regard porte sur un seul niveau (la cible de la
route trouvée n'est pas contrôlée à son tour), et les gardes de la cible
peuvent être évaluées deux fois : les règles doivent rester des prédicats
sans effet de bord.
Sans `RECURSIVE`, l'événement n'est pas réévalué dans la cible : aucun
contrôle de route n'a lieu.

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

`DEFINE STATE X 'libellé' AS @schema_X` (extension urban-workflow) relie
l'état au schéma YAML de ses champs métier, dans le même registre que les
schémas d'événements. Le socle de l'état (`Name`, `Uuid`, `CreationDate`,
`EventId`) est posé par le moteur et ne se redéfinit pas. Le **calcul**
des champs métier d'un état reste à venir : aujourd'hui ils sont modélisés
(schéma, contrôles, intellisense).

**Une instance d'état est créée à chaque passage par un `SWITCH`**, même
vers l'état courant (`Approuvee → Approuvee` crée une nouvelle instance),
avec un `Uuid` neuf, sa date d'entrée et l'`Uuid` de l'événement qui l'a
créée. Les instances sont conservées dans l'historique du workflow
(`workflow.states`, table SQL `workflow_states`).

Un bloc `ON EVENT nom` liste des **branches** (`switch_state`). À
l'arrivée de l'événement, les branches sont évaluées **dans l'ordre** ; la
**première** dont le `WHEN` est vrai (ou qui n'a pas de `WHEN`) est
appliquée, les suivantes sont ignorées. Une branche peut :

- changer d'état (`SWITCH cible`) — la cible doit exister, c'est vérifié
  au chargement ;
- exécuter des actions avant de changer d'état (`EXECUTE … SWITCH …`).

**Chaque branche se termine par un `SWITCH`.** La grammaire accepte une
branche faite seulement d'actions, mais le moteur la refuse au chargement
(`MissingStateError: missing state name`). Pour exécuter des actions sans
changer d'état, basculer vers l'état courant :

```sql
DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT Relance
        EXECUTE NotifierValideur(niveau = 'relance', dossier = @Workflow.ExternalId)
        SWITCH EnValidation        -- reste dans l'état (nouvelle instance d'état)
;
```

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

**Autant de fragments que nécessaire** — les `INCLUDE` s'empilent, un par
ligne, en tête du script :

```sql
INCLUDE 'evenements.wf'
INCLUDE 'regles.wf'
INCLUDE 'artefacts.wf'
NAME ValidationAchat VERSION 1
…
```

Ce qu'un fragment peut porter, et ce qu'il ne peut pas :

- un fragment ne contient que du **référentiel** : `DEFINE EVENT`,
  `DEFINE RULE`, `DEFINE ACTION`, `DEFINE ARTIFACT`, `DEFINE CONST` — pas
  d'état, pas d'initialiseur, pas de `VERSION`/`MATCHING`/`CONCURENCY` ;
- **pas d'inclusion en cascade** : un `INCLUDE` dans un fragment est une
  erreur de syntaxe ; chaque script complet liste tous ses fragments ;
- **la cible doit être un fragment** : inclure un workflow complet lève
  `FileNotFoundError: missing file …`, comme un fichier absent ;
- **l'inclusion n'est pas idempotente** : inclure deux fois le même
  fragment, ou deux fragments qui déclarent le même nom, lève
  `DuplicatedArgumentNameError` positionnée **sur le fragment fautif** ;
- chaque script complet est visité par un visiteur neuf : deux workflows
  partagent un fragment sans rien se partager d'autre ;
- **le script complet n'a pas besoin de déclaration propre** : il peut
  tirer la totalité de son référentiel des fragments inclus (jusqu'à la
  0.3.0 la grammaire en exigeait au moins une, et un tel script échouait
  sur `mismatched input 'INITIALIZE' expecting 'DEFINE'`) ; un
  **fragment**, lui, doit toujours déclarer quelque chose ;
- `parse_config()` sur une chaîne **ne résout pas** les `INCLUDE`, et ne
  le signale pas : les déclarations du fragment manquent, simplement. La
  résolution est le travail de `load_directory` (voir
  [guide-integration.md](guide-integration.md) §3).

## 10. Les erreurs

Le chargement échoue tôt, avec des messages positionnés
(`fichier:ligne:colonne`) :

| Erreur | Exemple de cause |
|---|---|
| `DslSyntaxError` | Syntaxe invalide, `;` manquant — chaque erreur porte fichier, ligne, colonne ; aussi pour une erreur de syntaxe **dans un script** (`montant_eleve.expr:2:5`) |
| `InvalidMethodReferenceError` | `EXECUTE Inconnue(…)` sans `DEFINE ACTION`, ou `WHEN RegleNonEnregistree(…)` |
| `InvalidArgumentNameError` | Argument absent de la signature déclarée |
| `MissingArgumentNameError` | Paramètre déclaré non fourni |
| `DuplicatedArgumentNameError` | Doublon : argument, paramètre, déclaration (état, événement, constante, artefact), initialiseur, événement d'un état, propriété `UNIQUE` |
| `InvalidArgumentValueError` | `'abc'` passé à un paramètre `INTEGER` ; chemin `@IncomingEvent.X` absent du schéma ; `@state` dans `INITIALIZE WORKFLOW` ; `@artifact.Inconnu` |
| `MissingStateError` | `SWITCH EtatInexistant`, ou branche sans `SWITCH` |
| `UnknownSchemaError` | `AS @schema` absent du `SchemaRegistry` |
| `UnknownScriptError` | `AS @script` ou `USING @script` absent du `ScriptRegistry` |

Pendant le traitement d'un événement, deux erreurs propres au langage
interrompent l'intégration (l'événement pourra être rejoué) :

| Erreur | Cause |
|---|---|
| `EventSchemaError` | le payload ne respecte pas le schéma de l'événement (`AS @schema`) |
| `ArtifactError` | le JSON produit par un artefact ne respecte pas son schéma, ou son script échoue |

Toutes héritent de `WorkflowError` et s'importent de
`urban_workflow.exceptions` ; la liste complète, avec les erreurs du
moteur, est au §8 de [guide-integration.md](guide-integration.md).

## 11. Aide-mémoire

```sql
NAME nom VERSION n                        -- identité
CONCURENCY n                              -- instances max par sujet
DESCRIPTION 'libellé'
MATCHING (K = 'v' …)                      -- routage des événements

DEFINE EVENT  Nom 'libellé' [AS @schema] [UNIQUE (Prop, …)];
DEFINE RULE   Nom (TYPE arg, …) 'libellé';     -- TYPE : TEXT|INTEGER|DECIMAL
DEFINE RULE   Nom (TYPE arg, …) 'libellé' AS @script;      -- méthode dans le ScriptRegistry
DEFINE ACTION Nom (TYPE arg, …) 'libellé';
DEFINE ARTIFACT Nom 'libellé' [AS @schema] USING @script;   -- JSON lu par @artifact.Nom
DEFINE CONST  nom valeur 'libellé';            -- valeur : 'txt' | 42 | n DAY

INITIALIZE WORKFLOW
    ON EVENT Nom [WHEN cond] [RECURSIVE] SWITCH Etat

DEFINE STATE Etat 'libellé'
    ON ENTER STATE | ON EXIT STATE | ON ENTER AND EXIT STATE
        [WHEN cond] [WAITING n UNITE BEFORE] actions
    ON EVENT Nom
        [WHEN cond] [actions] SWITCH Cible     -- branches dans l'ordre, la 1re vraie gagne
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

**Mots réservés** — interdits comme noms d'événement, d'état, de règle…
lorsqu'ils sont écrits en majuscules (les mots-clés sont sensibles à la
casse : `Etat` ou `state` restent libres) : `ACTION`, `AFTER`, `AND`, `ARTIFACT`, `AS`, `BEFORE`, `CONCURENCY`, `CONST`, `DAY`, `DECIMAL`, `DEFINE`, `DESCRIPTION`, `ENTER`, `EVENT`, `EXECUTE`, `EXIT`, `EXPIRE`, `FALSE`, `FRAGMENT`, `HOUR`, `IN`, `INCLUDE`, `INITIALIZE`, `INTEGER`, `IS`, `MATCHING`, `MINUTE`, `NAME`, `NOT`, `NULL`, `ON`, `OR`, `PARAMETER`, `RECURSIVE`, `RULE`, `STATE`, `STORE`, `SWITCH`, `TEXT`, `TIME`, `TRUE`, `UNIQUE`, `USING`, `VERSION`, `WAITING`, `WHEN`, `WITH`, `WORKFLOW`.
`PARAMETER`, `TIME` et `WITH` sont réservés par la grammaire sans être
utilisés aujourd'hui.

## 12. La grammaire, livrée avec le paquet

Le langage est décrit par deux grammaires ANTLR, **livrées dans la
distribution** (wheel et sdist) à côté du parseur généré :

```
urban_workflow/dsl/grammar/WorkflowLexer.g4    -- les mots et les symboles
urban_workflow/dsl/grammar/WorkflowParser.g4   -- les règles de structure
urban_workflow/dsl/grammar/regenerate.sh       -- régénère le parseur Python
```

Le parseur de `urban_workflow/dsl/generated/` est **du code généré commité**
— il ne se modifie jamais à la main. Pour toucher au langage : éditer les
`.g4`, puis

```bash
urban_workflow/dsl/grammar/regenerate.sh       # java >= 11 requis
```

Le script télécharge le jar ANTLR **4.13.2** s'il est absent (la même
version que le runtime `antlr4-python3-runtime` apporté par urban-json :
toute montée de version se fait des deux côtés à la fois). Il essaie
Maven Central puis un miroir — Maven Central limite parfois le débit
(429) — et `ANTLR_JAR=/chemin/vers.jar` court-circuite le téléchargement.
