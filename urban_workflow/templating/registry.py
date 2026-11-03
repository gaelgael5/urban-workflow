"""Registre des templates JSLT (portage de ``TemplateRepository``).

Un template par nom d'action, plus un template par défaut (l'équivalent de
``TemplateModels.DefaultAction``). Les templates viennent de chaînes JSLT
ou de fichiers ``.jslt`` d'un répertoire (le nom du fichier sans extension
est le nom d'action ; ``default.jslt`` définit le template par défaut).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

from urban_json import FunctionRegistry as JsltFunctionRegistry
from urban_json import JsltTemplate

from .. import constants

#: Template par défaut — même forme que ``TemplateModels.DefaultAction``.
DEFAULT_ACTION_TEMPLATE = """{
    "Uuid":       $.action.uuid,
    "Name":       $.action.name,
    "PushedAt":   $.now,
    "Arguments":  $.action.arguments,
    "WorkflowId": $.workflow.uuid,
    "EventId":    $.event.uuid,
    "From_State": $.event.from_state,
    "To_State":   $.event.to_state
}"""

#: Enveloppe des actions différées (``$_reminder``) ; le traducteur y
#: accroche le corps réel sous ``Message``.
REMINDER_TEMPLATE = """{
    "Uuid":     $.action.uuid,
    "Name":     $.action.name,
    "Kind":     $.action.kind,
    "Delay":    $.action.delay,
    "PushedAt": $.now
}"""

TemplateSource = Union[str, JsltTemplate]


def _compile(template: TemplateSource) -> JsltTemplate:
    if isinstance(template, JsltTemplate):
        return template
    return JsltTemplate.parse(template).build()


class TemplateRegistry:
    """Résolution nom d'action → template JSLT compilé, avec défaut.

    ``functions`` : registre urban-json de fonctions custom utilisables
    dans les templates (``None`` = fonctions intégrées).
    """

    def __init__(
        self,
        default_template: Optional[TemplateSource] = DEFAULT_ACTION_TEMPLATE,
        functions: Optional[JsltFunctionRegistry] = None,
    ) -> None:
        self.functions = functions
        self._templates: Dict[str, JsltTemplate] = {}
        self._default: Optional[JsltTemplate] = (
            _compile(default_template) if default_template is not None else None
        )
        # Enveloppe des rappels différés, remplaçable par add_template.
        self.add_template(constants.PUSH_REMINDER, REMINDER_TEMPLATE)

    # ------------------------------------------------------------------
    # Enregistrement
    # ------------------------------------------------------------------

    def add_template(self, action_name: str, template: TemplateSource) -> "TemplateRegistry":
        """Associe ``template`` à ``action_name`` (remplace, comme le source)."""
        self._templates[action_name] = _compile(template)
        return self

    def set_default(self, template: Optional[TemplateSource]) -> "TemplateRegistry":
        self._default = _compile(template) if template is not None else None
        return self

    def add_directory(
        self, path: Union[str, Path], pattern: str = "*.jslt"
    ) -> "TemplateRegistry":
        """Charge tous les fichiers ``pattern`` de ``path``.

        Le nom du fichier (sans extension) est le nom d'action ;
        ``default`` définit le template par défaut.
        """
        directory = Path(path)
        for item in sorted(directory.glob(pattern)):
            if not item.is_file():
                continue
            source = item.read_text(encoding="utf-8-sig")
            if item.stem == "default":
                self.set_default(source)
            else:
                self.add_template(item.stem, source)
        return self

    # ------------------------------------------------------------------
    # Résolution / application
    # ------------------------------------------------------------------

    def get(self, action_name: str) -> Optional[JsltTemplate]:
        """Le template de ``action_name``, sinon le template par défaut."""
        return self._templates.get(action_name, self._default)

    def __contains__(self, action_name: str) -> bool:
        return action_name in self._templates

    def transform(self, action_name: str, document: Any) -> Any:
        """Applique le template résolu au document de contexte."""
        template = self.get(action_name)
        if template is None:
            raise LookupError(
                f"no template registered for action {action_name!r} "
                "and no default template"
            )
        return template.transform(document, functions=self.functions)
