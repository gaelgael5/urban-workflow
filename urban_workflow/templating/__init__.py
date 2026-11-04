"""Templating urban-json (JSLT) des actions poussées.

Remplace le système de sortie du source (``TemplateRepository`` à réflexion
→ ``DynObject`` → ``Message*`` → Newtonsoft, cf. ``docs/analyse-portage.md``
§3) : un **document JSON de contexte** par action, un **template JSLT par
nom d'action** (fichiers ``.jslt`` + template par défaut), des en-têtes en
simple dict.

Branchement sur le moteur via la couture ``ActionTranslator`` de l'étape 3 ::

    from urban_workflow import WorkflowProcessor
    from urban_workflow.templating import JsltActionTranslator, TemplateRegistry

    templates = TemplateRegistry().add_directory("templates/")
    processor = WorkflowProcessor(
        configs, factory, translator=JsltActionTranslator(templates)
    )

Ce sous-paquet importe ``urban_json`` ; il n'est volontairement pas
réexporté par la racine du paquet (comme ``urban_workflow.dsl``).
"""

from .context import build_action_document, json_safe
from .metadata import MetadataRegistry
from .registry import (
    DEFAULT_ACTION_TEMPLATE,
    REMINDER_TEMPLATE,
    TemplateRegistry,
)
from .translator import JsltActionTranslator

__all__ = [
    "DEFAULT_ACTION_TEMPLATE",
    "JsltActionTranslator",
    "MetadataRegistry",
    "REMINDER_TEMPLATE",
    "TemplateRegistry",
    "build_action_document",
    "json_safe",
]
