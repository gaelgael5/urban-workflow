"""Configuration des règles conditionnées et des actions à produire."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..clock import WorkflowClock
from ..models import ResultAction, RuleSpan, RunContext
from ..values import ContextValue, make_value

#: Une règle ``WHEN`` compilée : prédicat sur le contexte d'exécution.
Rule = Callable[[RunContext], bool]


@dataclass
class DeclaredEventConfig:
    """Événement déclaré (``DEFINE EVENT``) ou technique.

    ``schema_ref`` porte le nom donné après ``AS @…`` ; quand un
    :class:`~urban_workflow.schemas.SchemaRegistry` est fourni au
    visiteur, ``schema`` et ``dedup_keys`` sont résolus au chargement et
    le moteur valide chaque événement entrant (et applique l'anti-doublon
    ``x-dedup``).
    """

    name: str = ""
    label: str = ""
    schema_ref: str = ""
    schema: dict[str, Any] | None = None
    dedup_keys: list[str] = field(default_factory=list)


@dataclass
class DeclaredArtifactConfig:
    """Artefact JSON nommé (``DEFINE ARTIFACT X 'l' AS @schema USING @script``).

    ``script_ref`` : script du ScriptRegistry qui produit le JSON (langage
    ``jslt`` en général) ; ``schema_ref``/``schema`` : JSON Schema facultatif
    qui valide le JSON produit (résolu si un SchemaRegistry est fourni).
    Consommé par le chemin ``@artifact.X`` dans les arguments d'action.
    """

    name: str = ""
    label: str = ""
    schema_ref: str = ""
    schema: dict[str, Any] | None = None
    script_ref: str = ""


@dataclass
class ResultActionConfig:
    """Action à produire (``EXECUTE action(args)`` / ``STORE (…)``)."""

    name: str = ""
    label: str = ""
    delay: int = 0
    kind: str = ""
    arguments: dict[str, ContextValue] = field(default_factory=dict)

    def add_argument(self, key: str, value: Any) -> ResultActionConfig:
        """Ajoute un argument ; les chaînes ``@a.b.c`` deviennent des références."""
        self.arguments[key] = make_value(value)
        return self

    def map(self, ctx: RunContext) -> ResultAction:
        """Instancie l'action pour un contexte donné (arguments non résolus)."""
        return ResultAction(
            name=self.name,
            label=self.name,
            delay=self.delay,
            kind=self.kind,
            event=ctx.event,
            event_date=WorkflowClock.now(),
            arguments=dict(self.arguments),
        )


@dataclass
class ResultRuleConfig:
    """Un bloc ``WHEN règle → actions`` (règle absente = toujours vrai)."""

    when_rule: Rule | None = None
    when_rule_text: str = ""
    when_rule_code: str = ""
    when_rule_position: RuleSpan = field(default_factory=RuleSpan.none)
    actions: list[ResultActionConfig] = field(default_factory=list)

    def add_actions(self, *actions: ResultActionConfig) -> ResultRuleConfig:
        self.actions.extend(actions)
        return self


def append_rule_actions(
    rules: list[ResultRuleConfig],
    when_rule: Rule | None,
    *actions: ResultActionConfig,
) -> ResultRuleConfig:
    """Accroche ``actions`` au bloc portant ``when_rule``, créé au besoin.

    Reprend le comportement des extensions ``AddAction``/``AddIncomingActions``
    du source : les actions partageant la même règle sont regroupées.
    """
    for rule in rules:
        if rule.when_rule is when_rule:
            rule.add_actions(*actions)
            return rule
    rule = ResultRuleConfig(when_rule=when_rule)
    rule.add_actions(*actions)
    rules.append(rule)
    return rule
