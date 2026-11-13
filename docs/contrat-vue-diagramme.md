# Contrat — vue diagramme et inclusions (cible 0.4.0)

Réponse à une demande d'évolution : *sortir la vue diagramme du modèle de
surface*, pour un back-office de paramétrage qui intègre urban-workflow
0.2.1 et offre deux vues sur un même workflow — une vue TEXTE (le script
DSL) et une vue DIAGRAMME, entre lesquelles l'utilisateur bascule.

La disposition de l'appelant suit le mécanisme de `load_directory` : le
référentiel de types d'événement d'un périmètre vit dans un script
`FRAGMENT`, que chaque workflow `INCLUDE`.

Ce document décrit **l'API et son contrat**. Il ne prescrit ni disposition
de fichiers, ni stockage, ni interface.

## 1. Le constat, mesuré

Le parseur accepte déjà les inclusions. Sur un workflow qui inclut un
fragment, avec urban-workflow 0.3.0 :

```
=== script à INCLUDE ===
  erreurs      : []
  is_fragment  : False
  includes     : ['referentiel_achat.wf']
=== extract_surface sur ce même script ===
  SurfaceError: les scripts à INCLUDE ne sont pas représentables en diagramme
```

Le refus vient **uniquement** de `extract_surface`
(`urban_workflow/dsl/surface.py`) : `WorkflowScriptParser` expose déjà
`includes` et `is_fragment` (`urban_workflow/dsl/parser.py:73-80`). Ni la
grammaire ni le parseur ne sont en cause pour ce point précis.

Conséquence pratique côté appelant : le fragment non dessinable ne gêne
pas (un référentiel n'a pas d'états), mais **tout workflow qui inclut le
référentiel porte un `INCLUDE`, donc aucun workflow réel ne se dessine**.

## 2. L'API cible

```python
extract_surface(source, filename="", fragments=None)   # -> SurfaceModel
render_script(model)                                   # -> str
place_missing_positions(model, layout)                 # -> document de positions
normalize_layout(data, workflow="")                    # -> document canonique
diff_layout(model, layout)                             # -> {missing, orphans}
```

- `fragments` est un mapping **en mémoire** `{nom: source}` : la
  bibliothèque ne lit ni n'écrit rien sur disque. L'appelant fournit les
  sources des fragments qu'il a déjà chargés.
- Omettre `fragments` reste légal : le modèle garde ses `INCLUDE` sans
  connaître leur contenu — même mode permissif que le visiteur sans
  registre de schémas.
- `FRAGMENT` et `INCLUDE` sont acceptés sans exception. Un fragment donne
  un modèle avec `is_fragment=True`, ses déclarations, et aucun état.

Le modèle gagne trois choses :

| Champ | Porté par | Sens |
|---|---|---|
| `includes: list[str]` | `SurfaceModel` | les cibles des `INCLUDE`, dans l'ordre |
| `is_fragment: bool` | `SurfaceModel` | script fragment ou script complet |
| `origin: str` | chaque déclaration | `""` = propre au script, sinon le nom du fragment |

## 3. `render_script` n'aplatit pas

C'est le cœur de la demande : une API qui accepte les inclusions en entrée
mais les inline en sortie fait perdre la factorisation au premier
enregistrement.

`render_script` émet les lignes `INCLUDE` avant `NAME` — ordre imposé par
la grammaire (`script_full` : `(INCLUDE CHAR_STRING)* NAME key …`) — et
**ne rend que les déclarations dont `origin == ""`**. Les déclarations
héritées d'un fragment ne sont jamais recopiées dans le script incluant.

### Point fixe

La propriété testée aujourd'hui, `render(extract(render(m))) ==
render(m)`, continue de valoir, inclusions comprises. Elle vaut même
**sans fournir les fragments** : puisque le rendu ignore les déclarations
héritées, la re-analyse du texte rendu n'a pas besoin de les connaître
pour produire le même texte.

Autrement dit : un appelant peut re-rendre un script sans relire le
référentiel. Les fragments n'enrichissent que la partie **lecture seule**
du modèle.

La limite documentée du modèle de surface — dans une branche sans garde
propre dont le premier bloc d'exécution commence par `WHEN`, la
re-analyse rattache ce `WHEN` à la branche — n'est pas touchée : elle vit
dans la re-analyse des `switch_state`, indépendante des inclusions. Les
cas à `INCLUDE` entrent dans la propriété de point fixe existante, ils ne
forment pas un test à côté.

## 4. Le document de positions

### Format

Le format existe déjà dans le playground ; il est remonté dans le cœur
**sans changement** :

```json
{"version": 1,
 "workflow": "ValidationAchat",
 "states": {"Tri": {"x": 280, "y": 60},
            "Approuvee": {"x": 600, "y": 100}}}
```

`normalize_layout` accepte aussi la forme courte `{"Tri": {"x": …, "y": …}}`,
valide que `x` et `y` sont des nombres finis (les booléens sont écartés
explicitement — en Python un `bool` est un `int`) et borne le document à
2000 états.

### La clé est le NOM de l'état

Ce n'est pas une préférence, c'est la seule option tenable. Un
identifiant généré devrait être stocké quelque part pour être retrouvé
après une édition en mode texte :

- dans le DSL — exclu : la mise en page reste hors du document de
  workflow, le DSL ne porte que la sémantique ;
- dans le document de positions — mais alors plus rien dans le script ne
  permet de rattacher l'identifiant à un état.

Un identifiant généré ne survivrait pas au premier aller-retour par le
texte. Le nom est la seule identité que le DSL porte.

### Comportement sur édition en mode texte

| Édition dans le texte | Position |
|---|---|
| État réordonné, déplacé dans le fichier | **conservée** — la clé ne dépend pas de l'ordre |
| État renommé | **perdue** : nouvelle clé absente, ancienne devenue orpheline — signalée |
| État supprimé | entrée orpheline **conservée** et signalée, jamais purgée en silence |
| État ajouté | sans position → placée par `place_missing_positions` |
| Renommage fait **dans le diagramme** | **conservée** — l'appelant renomme, donc il déplace la clé |

Réorganiser le texte ne brouille donc pas la mise en page ; seul un
**renommage en mode texte** la perd.

`diff_layout` rend `missing` (objets du script sans position) et
`orphans` (positions sans objet) pour que l'appelant puisse proposer
« l'état `Tri` a disparu, était-ce un renommage en `Aiguillage` ? ». La
bibliothèque ne devine pas : deviner déplacerait une boîte sans que
personne l'ait demandé, et une position orpheline ne coûte rien tant
qu'on ne la purge pas en silence.

### Positions manquantes

`place_missing_positions` ne touche **que** les objets sans position (les
autres gardent leur place) et applique un rangement en couches par
parcours en largeur. Il est **déterministe** : même script et même
document d'entrée donnent les mêmes positions.

Deux conséquences voulues : un document de positions vide suffit à
dessiner, et deux clients différents dessinent le même workflow de la
même façon.

## 5. Déclarations venues d'un `INCLUDE`

`origin` les rend **visibles** dans le modèle — l'appelant peut proposer
les événements du référentiel à la saisie — et le rendu les **exclut**
systématiquement du script incluant.

Reste le cas d'une déclaration héritée revenue **modifiée** dans le
modèle. La rendre serait aplatir ; l'ignorer serait perdre une saisie
sans un mot. Elle est donc **signalée en diagnostic** (« cette
déclaration appartient au référentiel `referentiel_achat.wf` »), à charge
de l'appelant de l'afficher. La bibliothèque ne peut pas rendre un champ
non éditable — c'est une affaire d'interface — mais elle peut refuser de
perdre l'information en silence.

## 6. Script syntaxiquement invalide

**Inchangé.** `DslSyntaxError` portant `errors: list[DslErrorModel]`,
chaque erreur avec `message`, `filename`, `line`, `column`, `start_index`
et `text`.

Une précision nouvelle : une erreur rencontrée dans un fragment porte
comme `filename` **la clé fournie dans `fragments`**, pour que l'éditeur
de l'appelant pointe le bon document.

`SurfaceError` ne sert plus pour `FRAGMENT` ni pour `INCLUDE`. Il subsiste
pour un modèle non rendable (section suivante).

## 7. Limite de grammaire à connaître

La grammaire exige **au moins une déclaration propre** dans le script
incluant (`WorkflowParser.g4:43` — `script_full : … (define_referenciel_statement SEMICOLON)+ …`).
Mesuré sur un workflow qui tire tout de son fragment :

```
sans.wf:5:0: mismatched input 'INITIALIZE' expecting 'DEFINE'
```

Tant que chaque workflow déclare ses propres `ACTION`, le cas ne se
présente pas. Mais un workflow dont le référentiel couvre *tout* est
**inécrivable aujourd'hui**, et l'API pourrait alors produire un script
non reparsable.

- `render_script` **refuse** de rendre un modèle sans déclaration propre,
  avec une erreur explicite, plutôt que d'émettre un script invalide.
- Lever la limite demande de relâcher `+` en `*` : extension de grammaire
  strictement élargissante (tout script valide aujourd'hui le reste),
  avec régénération du parseur ANTLR 4.13.2.

**Question ouverte à l'appelant** : avez-vous des workflows sans aucune
déclaration propre ? La réponse décide du relâchement.

## 8. Compatibilité et version

**Cible 0.4.0 — aucune rupture de signature.**

- `fragments` est un paramètre nommé optionnel ; les nouveaux champs du
  modèle sont additifs et `SurfaceModel.from_dict` est déjà tolérant.
- `normalize_layout` passe du playground au cœur, avec un ré-export
  conservé côté playground : rien ne casse pour ses utilisateurs.
- Un seul changement de comportement, assumé : un script à `FRAGMENT` ou
  à `INCLUDE` ne lève plus `SurfaceError`.

**Avertissement de montée de version** : passer de 0.2.1 à 0.4.0 traverse
la **0.3.0**, qui change un défaut du moteur — faute de `DedupKey` et de
`UNIQUE`, le moteur dédoublonne désormais quand même (`Uuid` du payload,
sinon `Name` + `EventDate` (+ `ExternalId`)). Un back-office qui
n'évalue pas n'est pas concerné ; le composant qui évalue, si.

## 9. Hors périmètre

- **Aucune persistance** : la bibliothèque reçoit et rend des documents
  en mémoire. Le stockage des scripts comme des positions appartient à
  l'appelant.
- **Aucune interface** : `place_missing_positions` est du calcul pur, pas
  du rendu graphique. Il est dans le cœur pour que deux vues ne divergent
  pas, pas pour imposer une représentation.
- **Aucune disposition de fichiers** imposée : `fragments` est un
  mapping, pas un répertoire.
