# Guide des règles écrites dans le DSL

> Référence du langage d'expressions des règles (`DEFINE RULE … AS …`).
> Le reste du DSL est décrit dans [guide-dsl.md](guide-dsl.md) ; les règles
> écrites en Python dans [guide-integration.md](guide-integration.md) §2.

## 1. Principe

Une règle est un **prédicat métier** utilisé par les conditions `WHEN`.
Elle peut être implémentée de deux façons, avec **la même syntaxe d'appel** :

| | Règle de code | Règle écrite dans le DSL |
|---|---|---|
| Déclaration | `DEFINE RULE R (DECIMAL seuil) 'l';` | `DEFINE RULE R (DECIMAL seuil) 'l' AS <expression>;` |
| Implémentation | callable Python enregistré dans le `FunctionRegistry` | l'expression après `AS` |
| Appel | `WHEN R(seuil = '1000')` | `WHEN R(seuil = '1000')` |

Choisir le DSL pour une condition **lisible par le métier** et **sans effet
de bord** : comparer des montants, tester un canal, mesurer l'âge d'un état.
Garder Python pour ce qui demande un appel externe, une base de données ou
une logique algorithmique.

Une règle a un corps **ou** une fonction enregistrée, jamais les deux : le
même nom avec un corps et une fonction de code est refusé au chargement.

## 2. Écrire une règle

```sql
DEFINE RULE MontantEleve (DECIMAL seuil) 'le montant dépasse le seuil'
    AS @IncomingEvent.Montant > seuil;
```

- La signature (`TEXT`, `INTEGER`, `DECIMAL`) type les paramètres : un
  argument `'1000'` passé à un `DECIMAL` arrive dans l'expression comme un
  nombre.
- Le libellé est facultatif, comme pour toute règle.
- L'expression s'arrête au `;`.

### Plusieurs lignes et commentaires

**Le corps peut s'étendre sur autant de lignes que nécessaire.** Sauts de
ligne, espaces et commentaires (`-- …` jusqu'à la fin de la ligne,
`/* … */` sur plusieurs lignes) sont permis partout entre `AS` et le `;`,
y compris au milieu d'une liste `IN` ou des arguments d'une fonction :

```sql
DEFINE RULE Eligible (DECIMAL seuil, INTEGER jours) 'dossier éligible au traitement rapide'
    AS -- un client fidèle compte double
       (@IncomingEvent.Montant * 2 > seuil OR @IncomingEvent.Fidele = TRUE)
       /* canaux dématérialisés uniquement */
       AND @IncomingEvent.Canal IN ('web',
                                    'mobile')
       AND DAYS_BETWEEN(@state.CreationDate, NOW()) < jours;
```

La présentation est libre : le moteur ne lit que les tokens. Convention
conseillée (c'est aussi celle du script généré par la vue Diagramme) :
`AS` sur sa propre ligne, indenté de 4 espaces, et les lignes suivantes
alignées sous le premier élément après `AS`, avec un opérateur `AND`/`OR`
en tête de ligne. Les erreurs indiquent la ligne exacte dans le corps.

## 3. Ce qu'une expression peut contenir

### Valeurs

| Écriture | Valeur |
|---|---|
| `42` | entier |
| `1.5` | décimal (le point est obligatoire des deux côtés : `0.5`, pas `.5`) |
| `'texte'` | texte ; une apostrophe s'écrit `''` : `'l''offre'` |
| `TRUE`, `FALSE` | booléens |
| `NULL` | absence de valeur |

Les nombres négatifs s'écrivent avec le moins unaire : `-5`.

### Références

| Écriture | Ce qu'elle désigne |
|---|---|
| `seuil` | un **paramètre** de la règle |
| `plafond_urgence` | une **constante** `DEFINE CONST`, même déclarée après la règle |
| `@IncomingEvent.Montant` | une propriété de l'événement entrant (socle + payload), avec `.Client.Pays`, `[0]`, `['nom']` |
| `@state.CreationDate` | l'instance de l'état du bloc où la règle est **appelée** (socle `Name`, `Uuid`, `CreationDate`, `EventId` et champs du schéma de l'état) |
| `@Workflow.ExternalId` | les autres chemins `@` du DSL ([guide-dsl.md](guide-dsl.md) §4) |

Un paramètre masque une constante du même nom. **Un nom nu inconnu est une
erreur**, contrairement aux arguments d'appel où il devient un texte : dans
un corps, un texte prend toujours des apostrophes. Une faute de frappe
(`seuill`) ne devient donc pas silencieusement la chaîne `'seuill'`.

### Opérateurs

| Famille | Opérateurs | Exemple |
|---|---|---|
| calcul | `-x`, `*`, `/`, `+`, `-` | `@IncomingEvent.Montant * 1.2 > plafond` |
| comparaison | `=`, `!=` (ou `<>`), `<`, `<=`, `>`, `>=` | `LENGTH(@IncomingEvent.Pieces) >= minimum` |
| appartenance | `x IN (a, b, …)`, `x NOT IN (…)` | `@IncomingEvent.Offre IN ('basic', 'premium')` |
| absence | `x IS NULL`, `x IS NOT NULL` | `@IncomingEvent.Montant IS NULL` |
| logique | `NOT`, `AND`, `OR`, parenthèses | `NOT (a OR b)` |

**Priorités**, de la plus forte à la plus faible :

1. moins unaire `-x` ;
2. `*` `/` ;
3. `+` `-` ;
4. comparaisons, `IN`, `IS NULL` ;
5. `NOT` ;
6. `AND` ;
7. `OR`.

`NOT a = b` se lit `NOT (a = b)`, et `a OR b AND c` se lit `a OR (b AND c)`.
En cas de doute, mettre des parenthèses.

`/` est une division décimale : `7 / 2` vaut `3.5`. `+` entre deux textes
les concatène.

Les mots-clés s'écrivent en **majuscules** (`AND`, `IN`, `NULL`…). `IN`,
`IS`, `NULL`, `TRUE` et `FALSE` sont des mots réservés du DSL : ils ne
peuvent plus servir de noms.

### Fonctions

Les noms de fonctions ne tiennent pas compte de la casse (`now()` =
`NOW()`).

| Fonction | Résultat | Exemple |
|---|---|---|
| `NOW()` | date et heure courantes (horloge du moteur, `WorkflowClock`) | `@IncomingEvent.Echeance < NOW()` |
| `DAYS_BETWEEN(debut, fin)` | nombre de jours (décimal) de `debut` à `fin` ; négatif si `fin` précède `debut` | `DAYS_BETWEEN(@state.CreationDate, NOW()) >= 3` |
| `HOURS_BETWEEN(debut, fin)` | idem en heures | `HOURS_BETWEEN(@IncomingEvent.EventDate, NOW()) < 24` |
| `MINUTES_BETWEEN(debut, fin)` | idem en minutes | |
| `LENGTH(x)` | longueur d'un texte, d'une liste ou d'un objet ; `NULL` pour autre chose | `LENGTH(@IncomingEvent.Pieces) >= 2` |
| `CONTAINS(conteneur, element)` | texte : sous-chaîne ; liste : élément présent ; objet : clé présente | `CONTAINS(@IncomingEvent.Libelle, 'urgent')` |

Une fonction inconnue ou un nombre d'arguments faux est refusé au
chargement.

## 4. Sémantique : une règle ne fait jamais échouer le traitement

Un événement mal formé ne doit pas interrompre le moteur. Les données
imprévues donnent donc une valeur, jamais une exception :

| Situation | Résultat |
|---|---|
| propriété absente du document (`@IncomingEvent.Inexistant`) | `NULL` |
| comparaison d'ordre (`<`, `>`…) avec `NULL` ou des types incompatibles (`5 > 'a'`) | faux |
| `=` entre types différents (`5 = '5'`) | faux ; `!=` vrai |
| calcul avec `NULL`, types incompatibles ou division par zéro | `NULL`, ce qui rend fausse la comparaison qui suit |
| `NULL` lu par `AND`, `OR` ou `NOT` | faux (donc `NOT x` est vrai quand `x` vaut `NULL`) |
| `x IN (…)` avec `x` à `NULL` | vrai seulement si la liste contient `NULL` |

Conséquence à connaître : `NOT (@IncomingEvent.Montant > 100)` est **vrai**
quand `Montant` est absent. Pour exiger la présence, l'écrire :
`@IncomingEvent.Montant IS NOT NULL AND @IncomingEvent.Montant <= 100`.

**Pas de conversion implicite des données de l'événement.** Les valeurs
arrivent avec leur type JSON : un montant envoyé en texte (`"Montant":
"1500"`) n'est pas un nombre, et `> 1000` est faux. C'est le rôle du
schéma de l'événement (`AS @schema`) de garantir les types.

**Dates.** Dans les documents, les dates sont des textes ISO 8601
(`2026-11-05T10:00:00Z`). Elles sont converties en dates dès que l'autre
côté d'une comparaison est une date (`NOW()`), et par les fonctions
`*_BETWEEN`. Deux textes restent comparés comme des textes. Une date sans
fuseau comparée à une date avec fuseau donne faux (ou `NULL` pour un écart).

## 5. Contrôles au chargement

Le script est refusé, avec une erreur positionnée (`fichier:ligne:colonne`),
si :

- le corps contient une erreur de syntaxe ;
- il utilise un nom qui n'est ni un paramètre ni une constante ;
- il appelle une fonction inconnue, ou avec un mauvais nombre d'arguments ;
- la règle a un corps et une fonction de code du même nom ;
- un appel oublie un paramètre déclaré, ou en passe un inconnu.

Le corps est ensuite **recompilé à chaque appel**, dans le contexte du bloc
appelant :

- `@state` désigne l'état du `DEFINE STATE` où se trouve l'appel ; il est
  refusé si la règle est appelée dans `INITIALIZE WORKFLOW` (aucun état
  n'existe encore) ;
- un chemin `@IncomingEvent.…` est contrôlé contre le schéma de l'événement
  du bloc `ON EVENT` appelant, quand un registre de schémas est fourni.

L'erreur pointe alors l'endroit du corps et cite l'appel :
`… (in rule 'Relancable' called at workflow.wf:24:12)`. Une même règle peut
donc être valide appelée dans un état et refusée dans un autre.

## 6. Exécution et journal

Chaque évaluation est tracée dans le journal du workflow comme une règle de
code, avec les valeurs des arguments :

```
MontantEleve(seuil=1000.0) -> True
```

**Une règle ne doit pas avoir d'effet de bord.** Le moteur peut l'évaluer
plusieurs fois pour un même événement : pour vérifier qu'un switch est
viable, il évalue d'avance les gardes de l'état cible. Les règles écrites
dans le DSL n'ont, par construction, aucun moyen de modifier quoi que ce
soit.

## 7. Exemples

```sql
-- Seuils et calcul
DEFINE CONST plafond_urgence 5000 'plafond de traitement urgent';
DEFINE RULE Urgente (DECIMAL plafond) 'réclamation urgente'
    AS CONTAINS(@IncomingEvent.Libelle, 'urgent')
       OR @IncomingEvent.Montant * 1.2 > plafond;

-- Liste de valeurs
DEFINE RULE OffreConnue () 'offre au catalogue'
    AS @IncomingEvent.Offre IN ('basic', 'premium', 'pro');

-- Données manquantes
DEFINE RULE SansMontant () 'montant non renseigné'
    AS @IncomingEvent.Montant IS NULL;

-- Âge de l'état courant (à appeler dans un DEFINE STATE)
DEFINE RULE Ancienne (INTEGER jours) 'dans l''état depuis assez longtemps'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= jours;

-- Engagement en mois, calculé en jours
DEFINE RULE EngagementTermine (INTEGER mois) 'engagement arrivé à terme'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= mois * 30;
```

Appels :

```sql
DEFINE STATE Tri 'tri'
    ON EVENT Reclamation
        WHEN Urgente(plafond = plafond_urgence) SWITCH Prioritaire
    ON EVENT Relance
        WHEN Ancienne(jours = '3') SWITCH EnTraitement
```

Le playground propose deux exemples complets à rejouer : « Règles écrites
dans le script » et « États et switch viable » (menu Exemples).

## 8. Dans le playground

- Une règle avec corps est évaluée pour de vrai : elle n'a pas besoin
  d'entrée dans le panneau Paramétrage. Si une règle du panneau porte le
  même nom, elle est ignorée et affichée barrée.
- Dans un corps, la complétion (`Ctrl`+`Espace`) propose les paramètres de
  la règle, les constantes, les fonctions, `@IncomingEvent.`, `@state.` et
  les opérateurs.
- Les erreurs sont soulignées à la ligne exacte du corps.
