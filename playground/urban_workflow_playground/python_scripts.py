"""Fonctions Python fournies par le playground (langage de script ``python``).

Décision utilisateur du 2026-11-08 : pas de nouveau langage ; les exemples
« autres qu'expression » sont des fonctions Python. Le playground n'exécute
JAMAIS de Python envoyé par le navigateur (serveur sans authentification,
joignable sur la machine de test) : comme une application réelle, il
enregistre lui-même ses fonctions par ``ScriptRegistry.add_function``. La vue
Scripts les montre en lecture seule (source et signature) et un workflow les
référence comme n'importe quel script : ``DEFINE RULE … AS @iban_valide``.

Ce qu'elles illustrent : la logique qu'une expression ne sait pas écrire
(contrôle de clé IBAN, expression régulière, calendrier des jours ouvrés).

Contrat d'une fonction de règle :

- ``(ctx, **params)`` — les noms des paramètres sont ceux de la
  déclaration ``DEFINE RULE`` (contrôlés au chargement) ; les valeurs
  arrivent déjà résolues et converties au type déclaré (``@IncomingEvent.X``
  → valeur, ``'3'`` déclaré INTEGER → ``3``) ;
- retourne un booléen et **ne lève pas** : une donnée absente ou mal
  formée donne ``False``, comme dans le langage ``expression`` ;
- aucun effet de bord : le moteur peut évaluer une garde plusieurs fois.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from urban_workflow import WorkflowClock


def iban_valide(ctx, iban):
    """Vrai si ``iban`` a une clé de contrôle correcte (ISO 13616, modulo 97)."""
    if not isinstance(iban, str):
        return False
    compact = iban.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", compact):
        return False
    # Les 4 premiers caractères passent à la fin, chaque lettre devient un
    # nombre (A=10 … Z=35) : l'IBAN est valide si le tout vaut 1 modulo 97.
    rearranged = compact[4:] + compact[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def email_valide(ctx, adresse):
    """Vrai si ``adresse`` a la forme d'une adresse électronique."""
    return isinstance(adresse, str) and _EMAIL.match(adresse.strip()) is not None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def jours_ouvres_depuis(ctx, depuis, jours):
    """Vrai si au moins ``jours`` jours ouvrés (lundi→vendredi) se sont
    écoulés entre ``depuis`` et maintenant (horloge du moteur)."""
    start = _as_datetime(depuis)
    if start is None or not isinstance(jours, int):
        return False
    now = WorkflowClock.now()
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    day: date = start.date()
    count = 0
    # Boucle jour par jour : un délai de règle se compte en jours ou en
    # semaines, pas en années — inutile d'optimiser.
    while day < now.date():
        day += timedelta(days=1)
        if day.weekday() < 5:
            count += 1
    return count >= jours


#: Fonctions enregistrées par le playground, sous ces noms de script.
PYTHON_SCRIPTS: dict[str, Callable[..., Any]] = {
    "iban_valide": iban_valide,
    "email_valide": email_valide,
    "jours_ouvres_depuis": jours_ouvres_depuis,
}


def describe() -> list[dict[str, Any]]:
    """Catalogue pour la vue Scripts : nom, paramètres, doc, source."""
    catalogue = []
    for name, func in PYTHON_SCRIPTS.items():
        params = list(inspect.signature(func).parameters)[1:]  # sans ctx
        catalogue.append({
            "name": name,
            "language": "python",
            "params": params,
            "doc": inspect.getdoc(func) or "",
            "source": inspect.getsource(func),
        })
    return catalogue
