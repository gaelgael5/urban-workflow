"""Schémas d'événements (JSON Schema écrits en YAML) et anti-doublon.

Les schémas vivent **à part** des scripts DSL : on les charge à
l'initialisation du moteur (fichiers YAML ou contenu brut) dans un
:class:`SchemaRegistry`, et les déclarations ``DEFINE EVENT … AS @nom``
les référencent par nom.

Chaque schéma décrit le payload complet de l'événement (socle commun
``Name``/``Uuid``/``ExternalId``/``CreationDate``/``EventDate`` + données
métier). Deux mots-clés propres à urban-workflow :

- ``x-dedup`` : liste de propriétés du payload dont la concaténation,
  hachée en SHA-256, identifie fonctionnellement l'événement — un
  événement entrant dont le hash existe déjà dans l'historique du
  workflow est ignoré (anti-doublon, en plus de l'anti-rejeu par Uuid).

La validation s'appuie sur les paquets optionnels PyYAML et jsonschema :
``pip install urban-workflow[schemas]``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .exceptions import DuplicatedArgumentNameError, EventSchemaError, UnknownSchemaError

#: Socle commun de tout événement — toujours validé en plus du schéma métier.
BASE_EVENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "urban-workflow base event",
    "type": "object",
    "properties": {
        "Name": {"type": "string", "minLength": 1},
        "Uuid": {"type": "string", "format": "uuid"},
        "ExternalId": {"type": "string"},
        "CreationDate": {"type": "string", "format": "date-time"},
        "EventDate": {"type": "string", "format": "date-time"},
    },
    "required": ["Name"],
}

#: Mot-clé (propre à urban-workflow) listant les propriétés de l'anti-doublon.
DEDUP_KEYWORD = "x-dedup"


def _load_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Les schémas d'événements nécessitent PyYAML : "
            "pip install urban-workflow[schemas]"
        ) from exc
    document = yaml.safe_load(text)
    if not isinstance(document, Mapping):
        raise EventSchemaError("un schéma YAML doit être un objet (mapping)")
    return dict(document)


def validate_document(schema: Mapping[str, Any], document: Mapping[str, Any]) -> None:
    """Valide ``document`` contre ``schema`` (+ formats uuid/date-time).

    Lève :class:`EventSchemaError` listant toutes les violations.
    """
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "La validation des événements nécessite jsonschema : "
            "pip install urban-workflow[schemas]"
        ) from exc

    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, format_checker=validator_cls.FORMAT_CHECKER)
    errors = [
        f"{'/'.join(str(p) for p in error.absolute_path) or '<racine>'}: {error.message}"
        for error in validator.iter_errors(dict(document))
    ]
    if errors:
        raise EventSchemaError(
            f"payload invalide pour le schéma "
            f"{schema.get('title') or schema.get('$id') or '?'} : "
            + " ; ".join(errors),
            errors=errors,
        )


def compute_dedup_hash(keys: Iterable[str], document: Mapping[str, Any]) -> str:
    """SHA-256 de la concaténation des propriétés ``keys`` du payload.

    Une propriété absente compte comme vide — deux événements qui ne
    diffèrent que par des propriétés hors ``keys`` ont le même hash.
    """
    material = "|".join(f"{key}={document.get(key, '')}" for key in keys)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class SchemaRegistry:
    """Registre nommé des schémas d'événements, chargé à l'initialisation.

    ::

        schemas = (
            SchemaRegistry()
            .add_directory("schemas/")            # un .yaml par schéma
            .add_yaml("myschema_Ping", "type: object")   # ou contenu brut
        )
        config = parse_config(script, rules=rules, schemas=schemas)
    """

    def __init__(self, include_base: bool = True) -> None:
        #: Si vrai, le socle :data:`BASE_EVENT_SCHEMA` est validé en plus
        #: de chaque schéma métier.
        self.include_base = include_base
        self._schemas: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Chargement (fichier, contenu, répertoire, dict)
    # ------------------------------------------------------------------

    def add_schema(self, name: str, schema: Mapping[str, Any]) -> SchemaRegistry:
        if name in self._schemas:
            raise DuplicatedArgumentNameError(f"schema {name!r} is already registered")
        self._schemas[name] = dict(schema)
        return self

    def add_yaml(self, name: str, text: str) -> SchemaRegistry:
        """Enregistre un schéma depuis son contenu YAML brut."""
        return self.add_schema(name, _load_yaml(text))

    def add_file(self, path: str | Path, name: str | None = None) -> SchemaRegistry:
        """Charge un fichier YAML ; le nom par défaut est le nom du fichier."""
        path = Path(path)
        return self.add_yaml(name or path.stem, path.read_text(encoding="utf-8-sig"))

    def add_directory(
        self, path: str | Path, pattern: str = "*.yaml"
    ) -> SchemaRegistry:
        for item in sorted(Path(path).glob(pattern)):
            if item.is_file():
                self.add_file(item)
        return self

    # ------------------------------------------------------------------
    # Résolution / validation
    # ------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        return name in self._schemas

    def names(self) -> list[str]:
        return sorted(self._schemas)

    def get(self, name: str) -> dict[str, Any]:
        try:
            return self._schemas[name]
        except KeyError:
            raise UnknownSchemaError(
                f"no schema registered under name {name!r}; "
                f"known: {self.names()}"
            ) from None

    def dedup_keys(self, name: str) -> list[str]:
        """Les propriétés ``x-dedup`` du schéma (liste vide si absentes)."""
        keys = self.get(name).get(DEDUP_KEYWORD, [])
        return [str(key) for key in keys]

    def validate(self, name: str, document: Mapping[str, Any]) -> None:
        """Valide un payload contre le socle commun puis le schéma ``name``."""
        if self.include_base:
            validate_document(BASE_EVENT_SCHEMA, document)
        validate_document(self.get(name), document)
