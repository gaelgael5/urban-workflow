# Guide des règles et de leurs scripts

> Comment une règle du DSL référence sa méthode (`DEFINE RULE … AS @script`),
> comment charger les scripts, et la référence du langage `expression`.
> Le reste du DSL est décrit dans [guide-dsl.md](guide-dsl.md) ; les règles
> de code dans [guide-integration.md](guide-integration.md) §2.

## 1. Principe : le workflow référence, le script implémente

Le document de workflow décrit le **métier** (états, transitions,
conditions) ; il ne porte pas de code. Une règle y déclare son nom, sa
signature typée et, avec `AS @nom`, **la méthode qui l'implémente** :

```sql
DEFINE RULE MontantEleve (DECIMAL seuil) 'le montant dépasse le seuil' AS @montant_eleve;
```

Le script `montant_eleve` vit à côté, dans un **registre de scripts**
chargé à l'initialisation du moteur, comme les schémas d'événements :

```sql
-- scripts/montant_eleve.expr
@IncomingEvent.Montant > seuil
```

Ce découpage apporte trois choses :

- **le choix du langage** de chaque méthode, fait au chargement : langage
  `expression` fourni, fonction Python, ou tout autre langage enregistré.
  Le workflow ne change pas quand on change d'implémentation ;
- **la réutilisation** : plusieurs règles peuvent référencer le même script ;
- **l'uniformité** avec les actions, qui référencent leur méthode de la
  même façon (`DEFINE ACTION … AS @script`, voir §2).

| Déclaration | Implémentation cherchée |
|---|---|
| `DEFINE RULE R (…) 'l';` | callable Python enregistré sous `R` dans le `FunctionRegistry` (comportement d'origine) |
| `DEFINE RULE R (…) 'l' AS @nom;` | script `nom` du `ScriptRegistry` |

L'appel est identique dans les deux cas : `WHEN R(seuil = '1000')`. Une
règle a un script **ou** une fonction de code sous son nom, jamais les
deux : le chargement refuse ce doublon.

## 2. Référencer un script dans le DSL

```sql
DEFINE RULE   Urgente (DECIMAL plafond) 'réclamation urgente' AS @urgente;
DEFINE RULE   Ancienne (INTEGER jours) 'dans l''état depuis longtemps'
    AS @regles.anciennete;
DEFINE ACTION Archiver (TEXT dossier) 'archivage du dossier' AS @archiver;
```

- `AS @nom` se place après le libellé facultatif.
- Le nom peut contenir des points (`@regles.anciennete`) pour ranger les
  scripts par thème.
- Le script utilise les **paramètres de la déclaration** qui le référence
  (`plafond`, `jours`) : c'est la déclaration qui fixe leurs noms et leurs
  types. Un argument `'1000'` passé à un `DECIMAL` arrive dans le script
  comme un nombre.
- **Actions :** la référence est acceptée et vérifiée au chargement, mais
  l'exécution des méthodes d'action reste à cadrer. Aujourd'hui, elle n'a
  pas d'effet et l'action produit son message comme avant (template JSLT).

## 3. Charger les scripts : le `ScriptRegistry`

```python
from urban_workflow.dsl import parse_config
from urban_workflow.scripts import ScriptRegistry

scripts = (
    ScriptRegistry()
    .add_directory("scripts/")                    # un fichier par script
    .add_file("communs/plafond.expr", name="regles.plafond")
    .add_script("canal_numerique", "@IncomingEvent.Canal IN ('web', 'mobile')")
    .add_function("solvable", lambda ctx, client: verifier_solvabilite(client))
)
config = parse_config(workflow_text, rules=rules, schemas=schemas, scripts=scripts)
```

| Méthode | Effet |
|---|---|
| `add_directory(chemin)` | charge les fichiers dont l'extension correspond à un langage connu ; les autres sont ignorés |
| `add_file(chemin, name=None)` | charge un fichier ; langage = extension, nom = nom du fichier sans extension |
| `add_script(nom, texte, language="expression")` | enregistre un script depuis son texte |
| `add_function(nom, callable)` | enregistre un callable Python `(ctx, **params)` |
| `register_language(langage)` | ajoute un langage |

Le **contrôle de syntaxe** a lieu dès l'enregistrement : un script mal
écrit lève une `DslSyntaxError` positionnée dans son fichier
(`scripts/urgente.expr:2:5`). Un nom enregistré deux fois est refusé.

### Langages fournis

| Langage | Source | Fonctionnement |
|---|---|---|
| `expression` | fichiers `.expr`, ou `add_script` | une expression booléenne, décrite §4 |
| `python` | `add_function` uniquement | le callable reçoit le contexte puis les arguments nommés ; sa signature est contrôlée contre celle de la déclaration au chargement |

Aucun fichier `.py` n'est exécuté par le registre : charger du code Python
reste une décision de l'application, qui enregistre ensuite ses fonctions.

### Écrire une règle en Python

Quand la logique dépasse ce qu'une expression sait dire (clé de contrôle,
expression régulière, calendrier, appel à un service interne), la règle
référence une fonction Python que l'application enregistre :

```python
import re
from urban_workflow import WorkflowClock

def iban_valide(ctx, iban):
    """Clé IBAN correcte (ISO 13616, modulo 97)."""
    if not isinstance(iban, str):
        return False                       # absent ou mal typé : False
    compact = iban.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", compact):
        return False
    chiffres = "".join(str(int(c, 36)) for c in compact[4:] + compact[:4])
    return int(chiffres) % 97 == 1

def email_valide(ctx, adresse):
    return isinstance(adresse, str) and re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$",
                                                 adresse.strip()) is not None

def jours_ouvres_depuis(ctx, depuis, jours):
    """Au moins `jours` jours ouvrés entre `depuis` et maintenant."""
    ...                                    # WorkflowClock.now(), jamais datetime.now()

scripts = (
    ScriptRegistry()
    .add_directory("scripts/")             # les .expr
    .add_function("iban_valide", iban_valide)
    .add_function("email_valide", email_valide)
    .add_function("jours_ouvres_depuis", jours_ouvres_depuis)
)
```

```sql
DEFINE RULE IbanValide (TEXT iban)      'clé IBAN correcte'   AS @iban_valide;
DEFINE RULE EmailValide (TEXT adresse)  'adresse bien formée' AS @email_valide;
DEFINE RULE DelaiDepasse (TEXT depuis, INTEGER jours) 'jours ouvrés écoulés'
    AS @jours_ouvres_depuis;

DEFINE STATE Controle 'contrôle'
    ON EVENT DemandeOuverture
        WHEN NOT IbanValide(iban = @IncomingEvent.Iban) SWITCH Rejetee
        WHEN NOT EmailValide(adresse = @IncomingEvent.Email) SWITCH AttenteCoordonnees
        SWITCH Ouvert
;
DEFINE STATE AttenteDepot 'dépôt attendu'
    ON EVENT Relance
        WHEN DelaiDepasse(depuis = @state.CreationDate, jours = '10') SWITCH Rejetee
;
```

Le contrat d'une fonction de règle :

- **Signature** : `(ctx, **params)`, avec exactement les noms de paramètres
  de la déclaration. C'est contrôlé au chargement : `DEFINE RULE IbanValide
  (TEXT compte)` est refusé, la fonction attend `iban`.
- **Arguments résolus** : la fonction reçoit des valeurs, pas des chemins.
  `@IncomingEvent.Iban` arrive en texte (ou `None` s'il est absent),
  `jours = '10'` déclaré `INTEGER` arrive en `10`. Un chemin `@…` n'est pas
  converti : `@state.CreationDate` arrive en `datetime`. `ctx` (le
  `RunContext`) reste disponible pour le reste : `ctx.incoming_event`,
  `ctx.workflow`.
- **Jamais d'exception** : une donnée absente ou mal formée donne `False`,
  comme dans le langage `expression`. Une exception levée par la fonction
  interromprait le traitement de l'événement.
- **Aucun effet de bord** (voir §6), et l'heure lue par `WorkflowClock.now()`,
  la même horloge que `NOW()`.

Les deux langages se mélangent librement dans un même workflow : seul le
registre sait comment chaque script est écrit.

### Ajouter un langage

Un langage est une sous-classe de `ScriptLanguage` :

```python
from urban_workflow.scripts import ScriptLanguage

class JsltLanguage(ScriptLanguage):
    name = "jslt"
    extensions = (".jslt",)

    def check(self, script):           # à l'enregistrement : syntaxe
        compiler_jslt(script.source)

    def compile(self, script, binding):
        # binding.parameters : signature de la déclaration qui référence
        # binding.constants  : constantes du workflow
        template = compiler_jslt(script.source)
        return lambda run_ctx, params: template.evaluer(run_ctx, params)

scripts = ScriptRegistry().register_language(JsltLanguage()).add_directory("scripts/")
```

`compile` est appelé **à chaque site d'appel** de la règle, avec la
signature de la déclaration : c'est là qu'un langage contrôle les noms
utilisés par le script.

### Sans registre

Si `parse_config` ne reçoit pas de `scripts`, les références `AS @…` sont
gardées sans être résolues (même mode permissif que pour les schémas).
Mais **appeler** une règle à script est alors refusé, faute de quoi
l'évaluer : `rule 'R' is implemented by script @nom but no ScriptRegistry
was provided`.

## 4. Le langage `expression`

Un script `expression` contient **une seule expression**, qui donne le
résultat de la règle. Un `;` final est toléré.

### Plusieurs lignes et commentaires

Le script s'écrit sur autant de lignes que nécessaire. Les commentaires
`-- …` (jusqu'à la fin de la ligne) et `/* … */` sont permis partout :

```sql
-- urgente.expr : réclamation à traiter en priorité
CONTAINS(@IncomingEvent.Libelle, 'urgent')
    /* le montant majoré de 20 % dépasse le plafond */
    OR @IncomingEvent.Montant * 1.2 > plafond
```

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
| `seuil` | un **paramètre** de la déclaration qui référence le script |
| `plafond_urgence` | une **constante** `DEFINE CONST` du workflow, même déclarée après la règle |
| `@IncomingEvent.Montant` | une propriété de l'événement entrant (socle + payload), avec `.Client.Pays`, `[0]`, `['nom']` |
| `@state.CreationDate` | l'instance de l'état du bloc où la règle est **appelée** (socle `Name`, `Uuid`, `CreationDate`, `EventId` et champs du schéma de l'état) |
| `@Workflow.ExternalId` | les autres chemins `@` du DSL ([guide-dsl.md](guide-dsl.md) §4) |

Un paramètre masque une constante du même nom. **Un nom nu inconnu est une
erreur**, contrairement aux arguments d'appel du DSL où il devient un
texte : dans un script, un texte prend toujours des apostrophes. Une faute
de frappe (`seuill`) ne devient donc pas silencieusement la chaîne
`'seuill'`.

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

### Sémantique : une règle ne fait jamais échouer le traitement

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

Côté workflow, le chargement est refusé avec une erreur positionnée
(`workflow.wf:ligne:colonne`) si :

- `AS @nom` désigne un script absent du registre ;
- une règle a à la fois un script et une fonction de code sous son nom ;
- un appel oublie un paramètre déclaré, ou en passe un inconnu.

Chaque script de règle est ensuite contrôlé **contre la signature de
chaque déclaration qui le référence**, même si la règle n'est jamais
appelée, puis **recompilé à chaque appel**, dans le contexte du bloc
appelant :

- `@state` désigne l'état du `DEFINE STATE` où se trouve l'appel ; il est
  refusé si la règle est appelée dans `INITIALIZE WORKFLOW` (aucun état
  n'existe encore) ;
- un chemin `@IncomingEvent.…` est contrôlé contre le schéma de l'événement
  du bloc `ON EVENT` appelant, quand un registre de schémas est fourni.

Une erreur trouvée dans un script est positionnée **dans le script** et
cite l'endroit du workflow concerné :

```
scripts/urgente.expr:3:25: unknown identifier 'plafon'; parameters: ['plafond'], …
    (in rule 'Urgente' declared at workflow.wf:12:58)
scripts/anciennete.expr:1:13: @state is only available inside a DEFINE STATE block …
    (in rule 'Ancienne' called at workflow.wf:31:13)
```

Un même script peut donc être valide pour une règle et refusé pour une
autre (paramètres différents), ou valide appelé dans un état et refusé dans
`INITIALIZE WORKFLOW`.

## 6. Exécution et journal

Chaque évaluation est tracée dans le journal du workflow comme une règle de
code, avec les valeurs des arguments :

```
Urgente(plafond=5000.0) -> True
```

**Une règle ne doit pas avoir d'effet de bord.** Le moteur peut l'évaluer
plusieurs fois pour un même événement : pour vérifier qu'un switch est
viable, il évalue d'avance les gardes de l'état cible. Les scripts
`expression` n'ont, par construction, aucun moyen de modifier quoi que ce
soit ; une fonction Python doit respecter la même règle.

## 7. Exemple complet

Workflow :

```sql
NAME Reclamations VERSION 1
DEFINE EVENT  ReclamationDeposee 'une réclamation est déposée' AS @schema_Reclamation;
DEFINE EVENT  Relance 'le client relance';

DEFINE RULE   Urgente (DECIMAL plafond) 'réclamation urgente' AS @urgente;
DEFINE RULE   Ancienne (INTEGER jours) 'dans l''état depuis assez longtemps'
    AS @anciennete;
DEFINE CONST  plafond_urgence 5000 'au-delà : traitement prioritaire';

INITIALIZE WORKFLOW
    ON EVENT ReclamationDeposee RECURSIVE SWITCH Tri

DEFINE STATE Tri 'tri'
    ON EVENT ReclamationDeposee
        WHEN Urgente(plafond = plafond_urgence) SWITCH Prioritaire
        SWITCH EnAttente
;
DEFINE STATE EnAttente 'en attente'
    ON EVENT Relance
        WHEN Ancienne(jours = '3') SWITCH Prioritaire
;
DEFINE STATE Prioritaire 'prioritaire' ;
```

Scripts :

```sql
-- scripts/urgente.expr
CONTAINS(@IncomingEvent.Libelle, 'urgent')
    OR @IncomingEvent.Montant * 1.2 > plafond
```

```sql
-- scripts/anciennete.expr : @state = l'état du bloc appelant (EnAttente)
DAYS_BETWEEN(@state.CreationDate, NOW()) >= jours
```

Chargement :

```python
scripts = ScriptRegistry().add_directory("scripts/")
config = parse_config(workflow_text, schemas=schemas, scripts=scripts)
```

## 8. Dans le playground

- La vue **Scripts** liste les scripts référencés par le workflow (règles
  et actions) et ceux qui sont écrits mais inutilisés. Badges : « à
  écrire », « erreur », « inutilisé ».
- Le détail montre les déclarations qui utilisent le script et un éditeur
  avec complétion (`Ctrl`+`Espace`) : paramètres de ces déclarations,
  constantes, fonctions, `@IncomingEvent.…`, `@state.…`, opérateurs. Les
  erreurs sont soulignées dans le script, et aussi dans le workflow à
  l'endroit de la référence ou de l'appel.
- « écrire en script », sous la liste, transforme une règle sans script :
  le playground ajoute `AS @nom` à sa déclaration et crée le script.
- Dans l'éditeur du workflow, `AS @` après un `DEFINE RULE` ou un
  `DEFINE ACTION` propose les noms de scripts.
- Une règle à script n'a pas besoin d'entrée dans le panneau Paramétrage.
  Si une règle du panneau porte le même nom, elle est ignorée et affichée
  barrée.
- Les exemples « Règles et scripts » et « États et switch viable » sont
  complets et se rejouent tels quels.
- **Python** : le playground n'exécute jamais de Python envoyé par le
  navigateur (il n'a pas d'authentification). Comme une application, il
  enregistre lui-même trois fonctions (`@iban_valide`, `@email_valide`,
  `@jours_ouvres_depuis`, dans `urban_workflow_playground/python_scripts.py`),
  que la vue Scripts montre en lecture seule avec leurs paramètres. Leurs
  noms sont réservés, et un script envoyé avec un autre langage
  qu'`expression` est refusé avec une erreur. L'exemple « Scripts Python »
  les mélange avec un script `expression`.
