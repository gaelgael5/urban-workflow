"""Analyse syntaxique d'un script DSL (portage de ``WorkflowConfigParser``).

:class:`WorkflowScriptParser` encapsule le lexer/parseur générés par ANTLR :
il produit l'arbre syntaxique, collecte les erreurs de syntaxe positionnées,
calcule le CRC32 du contenu et expose les métadonnées nécessaires au
chargement (``INCLUDE`` du script, script fragment ou complet).
"""

from __future__ import annotations

import zlib
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from ..exceptions import DslSyntaxError
from .errors import DslErrorModel
from .generated.WorkflowLexer import WorkflowLexer
from .generated.WorkflowParser import WorkflowParser


def _unquote(text: str) -> str:
    """Retire les quotes d'une ``CHAR_STRING`` (``''`` est l'échappement de ``'``)."""
    text = text.strip()
    if len(text) >= 2 and text.startswith("'") and text.endswith("'"):
        text = text[1:-1].replace("''", "'")
    return text


class _CollectingErrorListener(ErrorListener):
    """Collecte les erreurs de syntaxe sous forme de :class:`DslErrorModel`."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.errors: list[DslErrorModel] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = offendingSymbol.text if offendingSymbol is not None else ""
        start_index = offendingSymbol.start if offendingSymbol is not None else 0
        self.errors.append(
            DslErrorModel(
                message=msg,
                filename=self.filename,
                line=line,
                column=column,
                start_index=start_index,
                text=text,
            )
        )


class WorkflowScriptParser:
    """Un script DSL analysé : arbre syntaxique + métadonnées.

    Construire via :meth:`parse_string` ou :meth:`parse_path`.
    """

    def __init__(
        self,
        tree: WorkflowParser.ScriptContext,
        *,
        filename: str,
        content: str,
        errors: list[DslErrorModel],
    ) -> None:
        self.tree = tree
        self.filename = filename
        self.content = content
        self.errors = errors
        self.crc = zlib.crc32(content.encode("utf-8"))

        fragment = tree.script_fragment()
        self.is_fragment = fragment is not None

        self.includes: list[str] = []
        if not self.is_fragment:
            full = tree.script_full()
            if full is not None and full.INCLUDE():
                self.includes = [_unquote(item.getText()) for item in full.CHAR_STRING()]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def parse_string(cls, source: str, filename: str = "") -> WorkflowScriptParser:
        """Analyse ``source`` ; les erreurs de syntaxe sont collectées dans ``errors``."""
        listener = _CollectingErrorListener(filename)

        lexer = WorkflowLexer(InputStream(source))
        lexer.removeErrorListeners()
        lexer.addErrorListener(listener)

        parser = WorkflowParser(CommonTokenStream(lexer))
        parser.removeErrorListeners()
        parser.addErrorListener(listener)

        tree = parser.script()

        return cls(tree, filename=filename, content=source, errors=listener.errors)

    @classmethod
    def parse_path(cls, path: str | Path) -> WorkflowScriptParser:
        """Analyse le fichier ``path`` (UTF-8, BOM toléré)."""
        path = Path(path)
        content = path.read_text(encoding="utf-8-sig")
        return cls.parse_string(content, filename=str(path))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def check(self) -> WorkflowScriptParser:
        """Lève :class:`DslSyntaxError` si des erreurs de syntaxe ont été collectées."""
        if self.errors:
            details = "; ".join(str(error) for error in self.errors)
            raise DslSyntaxError(
                f"{len(self.errors)} syntax error(s) in workflow script: {details}",
                errors=self.errors,
            )
        return self

    def visit(self, visitor) -> object | None:
        """Fait visiter l'arbre par ``visitor`` (positionne son ``filename``/``crc``)."""
        visitor.filename = self.filename
        visitor.crc = self.crc
        return visitor.visit(self.tree)
