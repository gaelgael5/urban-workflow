"""Erreurs positionnées du parseur DSL (portage de ``ErrorModel``)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DslErrorModel:
    """Une erreur de syntaxe positionnée dans un script DSL."""

    message: str = ""
    filename: str = ""
    line: int = 0
    column: int = 0
    start_index: int = 0
    text: str = ""

    def __str__(self) -> str:
        location = f"{self.filename}:{self.line}:{self.column}" if self.filename else (
            f"{self.line}:{self.column}"
        )
        return f"{location}: {self.message}"
