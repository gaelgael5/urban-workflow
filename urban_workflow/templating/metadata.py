"""Registre des métadonnées (en-têtes) par nom d'action.

Portage de ``MetadatRepository``. Différence assumée avec le source
(bug §5 non reproduit) : ``AddMetadata`` y indexait le dictionnaire interne
par ``key`` — le nom du template — au lieu de ``metadata.Key``, si bien que
toutes les métadonnées d'une action s'écrasaient entre elles. Ici, la
fusion se fait bien par clé de métadonnée.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional, Tuple, Union

Metadatas = Union[Mapping[str, str], Iterable[Tuple[str, str]]]


class MetadataRegistry:
    """En-têtes des messages poussés, par nom d'action, avec défaut."""

    def __init__(self, default: Optional[Metadatas] = None) -> None:
        self._default: Dict[str, str] = dict(default or {})
        self._by_action: Dict[str, Dict[str, str]] = {}

    def add_metadata(self, action_name: str, metadatas: Metadatas) -> "MetadataRegistry":
        """Fusionne ``metadatas`` dans les en-têtes de ``action_name``.

        La fusion est **par clé de métadonnée** : une clé déjà présente est
        remplacée, les autres sont conservées.
        """
        box = self._by_action.setdefault(action_name, {})
        box.update(dict(metadatas))
        return self

    def set_default(self, metadatas: Metadatas) -> "MetadataRegistry":
        self._default = dict(metadatas)
        return self

    def get(self, action_name: str) -> Dict[str, str]:
        """Copie des en-têtes de ``action_name``, sinon ceux par défaut."""
        box = self._by_action.get(action_name)
        return dict(box) if box is not None else dict(self._default)
