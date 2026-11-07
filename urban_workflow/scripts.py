"""Registre des scripts référencés par le DSL (``DEFINE RULE … AS @nom``).

Décision utilisateur du 2026-11-07 : le document de workflow ne porte pas
de code. Une règle (et, à terme, une action) **référence** sa méthode par
nom ; le script vit à côté, chargé à l'initialisation du moteur comme les
schémas (:class:`~urban_workflow.schemas.SchemaRegistry`) :

.. code-block:: python

    scripts = (
        ScriptRegistry()
        .add_directory("scripts/")                       # un fichier par script
        .add_script("montant_eleve", "@IncomingEvent.Montant > seuil")
        .add_function("solvable", lambda ctx, client: check(client))
    )
    config = parse_config(script, scripts=scripts)

Chaque script a un **langage**, qui sait le compiler. Deux langages sont
fournis :

- ``expression`` — le langage d'expressions des règles (fichiers ``.expr``,
  voir :mod:`urban_workflow.dsl.expressions`) ;
- ``python`` — un callable ``(ctx, **params)`` enregistré par
  :meth:`ScriptRegistry.add_function` (pas de fichier ``.py`` exécuté : le
  chargement de code reste du ressort de l'application).

D'autres langages s'ajoutent par :meth:`ScriptRegistry.register_language`
sans toucher au DSL : c'est l'intérêt de la référence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import DuplicatedArgumentNameError, UnknownScriptError

#: Méthode compilée : ``(run_ctx, params) -> valeur``.
CompiledScript = Callable[[Any, dict[str, Any]], Any]


@dataclass(frozen=True)
class Script:
    """Un script nommé du registre."""

    name: str
    language: str
    #: Texte source (langages textuels).
    source: str = ""
    #: Callable (langage ``python``).
    function: Callable[..., Any] | None = None
    #: Nom utilisé dans les positions d'erreur (``origine:ligne:colonne``) :
    #: chemin du fichier, sinon le nom du script.
    origin: str = ""

    @property
    def where(self) -> str:
        return self.origin or self.name


@dataclass
class ScriptBinding:
    """Ce que le chargeur du DSL fournit pour compiler un script à UN site
    d'appel : la signature de la déclaration qui le référence, les
    constantes du workflow, la fabrique de chemins ``@…`` (liée au bloc
    appelant : ``@state``, schéma de l'événement) et la levée d'erreurs
    positionnées DANS le script."""

    owner: str
    parameters: dict[str, type] = field(default_factory=dict)
    constants: dict[str, Any] = field(default_factory=dict)
    make_path: Callable[[str, Any], Any] | None = None
    error: Callable[[type, Any, str], Any] | None = None


class ScriptLanguage(ABC):
    """Un langage de script : contrôle à l'enregistrement, compilation à
    chaque site d'appel."""

    #: Nom du langage (``Script.language``).
    name: str = ""
    #: Extensions de fichier reconnues par :meth:`ScriptRegistry.add_file`.
    extensions: tuple[str, ...] = ()

    def check(self, script: Script) -> None:  # optionnel : rien par défaut
        """Contrôle à l'enregistrement (syntaxe) ; lève une erreur du moteur."""

    @abstractmethod
    def compile(self, script: Script, binding: ScriptBinding) -> CompiledScript:
        """Compile ``script`` pour la déclaration décrite par ``binding``."""


class PythonLanguage(ScriptLanguage):
    """Callable ``(ctx, **params)`` enregistré côté code."""

    name = "python"

    def check(self, script: Script) -> None:
        if not callable(script.function):
            raise TypeError(f"python script {script.name!r} needs a callable")

    def compile(self, script: Script, binding: ScriptBinding) -> CompiledScript:
        from .registry import FunctionRegistry

        # Même contrôle de signature qu'une règle de code : tous les
        # paramètres déclarés doivent être acceptés par le callable.
        FunctionRegistry(f"script for {binding.owner!r}").add(
            script.name, script.function
        ).validate_call(script.name, list(binding.parameters))
        func = script.function
        return lambda run_ctx, params: func(run_ctx, **params)


class ScriptRegistry:
    """Registre nommé des scripts, chargé à l'initialisation du moteur."""

    def __init__(self, languages: list[ScriptLanguage] | None = None) -> None:
        self._languages: dict[str, ScriptLanguage] = {}
        self._scripts: dict[str, Script] = {}
        if languages is None:
            # Import paresseux : le langage d'expressions vit dans le DSL,
            # qui importe lui-même ce module.
            from .dsl.expressions import ExpressionLanguage

            languages = [ExpressionLanguage(), PythonLanguage()]
        for language in languages:
            self.register_language(language)

    # ------------------------------------------------------------------
    # Langages
    # ------------------------------------------------------------------

    def register_language(self, language: ScriptLanguage) -> ScriptRegistry:
        if language.name in self._languages:
            raise DuplicatedArgumentNameError(
                f"script language {language.name!r} is already registered"
            )
        self._languages[language.name] = language
        return self

    def language(self, name: str) -> ScriptLanguage:
        try:
            return self._languages[name]
        except KeyError:
            raise UnknownScriptError(
                f"unknown script language {name!r}; known: {sorted(self._languages)}"
            ) from None

    def _language_for(self, path: Path) -> ScriptLanguage | None:
        for language in self._languages.values():
            if path.suffix in language.extensions:
                return language
        return None

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def add(self, script: Script) -> ScriptRegistry:
        if script.name in self._scripts:
            raise DuplicatedArgumentNameError(
                f"script {script.name!r} is already registered"
            )
        self.language(script.language).check(script)
        self._scripts[script.name] = script
        return self

    def add_script(
        self, name: str, source: str, language: str = "expression", origin: str = ""
    ) -> ScriptRegistry:
        """Enregistre un script depuis son texte source."""
        return self.add(Script(name=name, language=language, source=source, origin=origin))

    def add_function(self, name: str, func: Callable[..., Any]) -> ScriptRegistry:
        """Enregistre un callable Python ``(ctx, **params)``."""
        return self.add(Script(name=name, language="python", function=func))

    def add_file(self, path: str | Path, name: str | None = None) -> ScriptRegistry:
        """Charge un fichier ; le langage vient de l'extension, le nom par
        défaut est le nom du fichier sans extension."""
        path = Path(path)
        language = self._language_for(path)
        if language is None:
            known = sorted(e for lang in self._languages.values() for e in lang.extensions)
            raise UnknownScriptError(
                f"no script language for {path.name!r}; known extensions: {known}"
            )
        return self.add_script(
            name or path.stem,
            path.read_text(encoding="utf-8-sig"),
            language=language.name,
            origin=str(path),
        )

    def add_directory(self, path: str | Path) -> ScriptRegistry:
        """Charge les fichiers du répertoire dont l'extension est connue."""
        for item in sorted(Path(path).iterdir()):
            if item.is_file() and self._language_for(item) is not None:
                self.add_file(item)
        return self

    # ------------------------------------------------------------------
    # Résolution
    # ------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        return name in self._scripts

    def names(self) -> list[str]:
        return sorted(self._scripts)

    def get(self, name: str) -> Script:
        try:
            return self._scripts[name]
        except KeyError:
            raise UnknownScriptError(
                f"no script registered under name {name!r}; known: {self.names()}"
            ) from None

    def compile(self, name: str, binding: ScriptBinding) -> CompiledScript:
        script = self.get(name)
        return self.language(script.language).compile(script, binding)
