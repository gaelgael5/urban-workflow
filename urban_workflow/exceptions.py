"""Hiérarchie d'exceptions du moteur.

Portage des exceptions du projet source ; ``WorkflowError`` est la racine
commune pour permettre un ``except WorkflowError`` global.
"""


class WorkflowError(Exception):
    """Racine de toutes les erreurs du moteur."""


class InvalidIncomingEventFormatError(WorkflowError):
    """Le payload de l'événement entrant n'a pas pu être désérialisé."""


class MissingConfigurationError(WorkflowError):
    """Aucune configuration ne correspond au nom/version demandés."""


class MissingStateError(WorkflowError):
    """Un ``SWITCH`` référence un état qui n'est pas défini."""


class LockFailedError(WorkflowError):
    """Le verrou d'un contexte d'exécution n'a pas pu être obtenu."""


class ResolutionArgumentError(WorkflowError):
    """Un chemin ``@a.b.c`` n'a pas pu être résolu dans le contexte."""


class InvalidMethodReferenceError(WorkflowError):
    """Une règle ou action est utilisée sans être enregistrée."""


class InvalidArgumentNameError(WorkflowError):
    """Un argument nommé ne correspond pas à la signature déclarée."""


class MissingArgumentNameError(WorkflowError):
    """Un argument requis par la signature n'a pas été fourni."""


class DuplicatedArgumentNameError(WorkflowError):
    """Un nom (argument, règle, action, état…) est déclaré deux fois."""


class InvalidArgumentValueError(WorkflowError):
    """Une valeur d'argument n'est pas convertible vers le type déclaré."""


class UnknownSchemaError(WorkflowError):
    """Un ``DEFINE EVENT … AS @schema`` référence un schéma non enregistré."""


class UnknownScriptError(WorkflowError):
    """Un ``DEFINE RULE/ACTION … AS @script`` référence un script non
    enregistré (ou un langage de script inconnu)."""


class EventSchemaError(WorkflowError):
    """Le payload d'un événement ne respecte pas le schéma déclaré.

    ``errors`` porte la liste lisible des violations.
    """

    def __init__(self, message: str, errors=None) -> None:
        super().__init__(message)
        self.errors = list(errors or [])


class DslSyntaxError(WorkflowError):
    """Le script DSL contient des erreurs de syntaxe.

    ``errors`` porte la liste des erreurs positionnées
    (:class:`urban_workflow.dsl.errors.DslErrorModel`).
    """

    def __init__(self, message: str, errors=None) -> None:
        super().__init__(message)
        self.errors = list(errors or [])
