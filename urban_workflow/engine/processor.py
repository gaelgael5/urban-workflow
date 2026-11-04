"""Processeur d'événements (portage de ``WorkflowProcessor<TContext>``).

Flux : contextes existants (par ``ExternalId``) + créations éventuelles
(Initializers + CONCURENCY) → évaluation des transitions et collecte des
actions → chaîne d'append → traduction des actions → chaîne de sorties
sous transaction.

Différences assumées avec le source :

- la garde CONCURENCY est **stricte** (``<`` au lieu de ``<=``) : le source
  autorisait une instance de plus que la limite déclarée ;
- le rejeu d'un événement déjà intégré (même uuid) ne recrée pas de
  workflow : le source ignorait le doublon côté transitions mais le
  laissait repasser par les Initializers ;
- la transaction est réellement annulée si l'exécution des sorties échoue
  (le ``Dispose`` du source n'annulait jamais — condition inversée).
"""

from __future__ import annotations

from collections.abc import Callable

from .. import constants
from ..config import (
    InitializationConfig,
    ResultRuleConfig,
    TransitionConfig,
    WorkflowConfig,
    WorkflowsConfig,
)
from ..models import IncomingEvent, RuleSpan, RunContext, Workflow
from ..outputs.base import OutputAction
from ..schemas import BASE_EVENT_SCHEMA, compute_dedup_hash, validate_document
from .append_events import AppendResultActionEvent, AppendStandardEvent
from .factory import WorkflowFactory
from .serializer import event_to_document
from .translator import ActionTranslator, DefaultActionTranslator


class WorkflowProcessor:
    """Évalue un événement entrant sur les workflows existants et à créer."""

    def __init__(
        self,
        config: WorkflowsConfig,
        factory: WorkflowFactory,
        *,
        translator: ActionTranslator | None = None,
    ) -> None:
        self._config = config
        self.factory = factory
        self.translator = translator or DefaultActionTranslator()

        #: Callback de chargement des workflows existants (storage).
        self.load_existing_workflows_by_external_id: Callable[[str], list[Workflow]] | None = None

        #: Fabrique de la chaîne de sorties (une chaîne neuve par évaluation).
        self.output_actions: Callable[[], OutputAction] | None = None

        # Chaîne de responsabilité : où insérer l'événement dans le modèle.
        self._append_event = AppendResultActionEvent(AppendStandardEvent())

    # ------------------------------------------------------------------
    # Point d'entrée
    # ------------------------------------------------------------------

    def evaluate_event(self, event: IncomingEvent) -> list[RunContext]:
        """Évalue ``event`` ; retourne les contextes impactés (utile aux tests)."""

        if event is None:
            raise ValueError("event is required")
        if self.output_actions is None:
            raise ValueError("output_actions is required")

        workflows = self._load_existing_workflows(event)
        contexts = list(self._get_existing_contexts(event, workflows))

        existing_by_name: dict[str, list[RunContext]] = {}
        for ctx in contexts:
            existing_by_name.setdefault(ctx.workflow.workflow_name, []).append(ctx)

        contexts.extend(
            self._evaluate_new_workflows(event, existing_by_name, workflows)
        )

        if contexts:

            for ctx in contexts:
                self._append_event.eval(ctx)

            self._translate_actions(contexts)

            output = self.output_actions()
            for ctx in contexts:
                output.prepare(ctx)

            transaction = output.begin_transaction()
            try:
                output.execute()
                transaction.commit()
            except BaseException:
                transaction.rollback()
                raise

        return contexts

    # ------------------------------------------------------------------
    # Workflows existants
    # ------------------------------------------------------------------

    def _load_existing_workflows(self, event: IncomingEvent) -> list[Workflow]:
        if self.load_existing_workflows_by_external_id is None:
            return []

        workflows = self.load_existing_workflows_by_external_id(event.external_id)

        # Un événement portant WorkflowId est restreint à ce workflow précis.
        workflow_id = event.extended_datas.get(constants.WORKFLOW_ID_PROPERTY)
        if workflow_id is not None:
            workflows = [w for w in workflows if str(w.uuid) == str(workflow_id)]

        return workflows

    def _get_existing_contexts(self, event: IncomingEvent, workflows: list[Workflow]):
        for workflow in workflows:
            config = self._check_and_resolve_config(workflow, event)
            if config is None:
                continue

            dedup_hash = self._event_gate(config, event)
            if dedup_hash and any(
                e.dedup_hash == dedup_hash for e in workflow.events
            ):
                continue  # doublon fonctionnel : ignoré, comme un rejeu

            ctx = self.factory.create_context(workflow, event)
            ctx.event.dedup_hash = dedup_hash
            ctx.event.to_state = ctx.event.from_state = workflow.current_state
            self._evaluate_event_in_current_workflow(config, ctx)

            yield ctx

    def _event_gate(self, config: WorkflowConfig, event: IncomingEvent) -> str:
        """Valide l'événement contre son schéma déclaré et retourne son
        empreinte anti-doublon (``""`` si aucun mécanisme ne s'applique).

        Priorité de l'empreinte : ``DedupKey`` fourni par l'émetteur,
        sinon hash des propriétés ``UNIQUE`` déclarées dans le DSL.
        La validation (socle commun + schéma métier) lève
        :class:`~urban_workflow.exceptions.EventSchemaError`.
        """
        declared = config.declared_events.get(event.name)
        if declared is None:
            return ""

        document = None
        if declared.schema is not None:
            document = event_to_document(event)
            validate_document(BASE_EVENT_SCHEMA, document)
            validate_document(declared.schema, document)

        if event.dedup_key:
            return compute_dedup_hash(
                (constants.DEDUP_KEY_PROPERTY,),
                {constants.DEDUP_KEY_PROPERTY: event.dedup_key},
            )
        if declared.dedup_keys:
            if document is None:
                document = event_to_document(event)
            return compute_dedup_hash(declared.dedup_keys, document)
        return ""

    @staticmethod
    def _already_integrated(
        workflow: Workflow, event: IncomingEvent, dedup_hash: str
    ) -> bool:
        """Rejeu technique (même Uuid) ou doublon fonctionnel (même hash)."""
        if workflow.get_event(event.uuid) is not None:
            return True
        return bool(dedup_hash) and any(
            e.dedup_hash == dedup_hash for e in workflow.events
        )

    def _check_and_resolve_config(
        self, workflow: Workflow, event: IncomingEvent
    ) -> WorkflowConfig | None:
        # Un événement ne peut pas être intégré deux fois.
        if workflow.get_event(event.uuid) is not None:
            return None

        # Lève MissingConfigurationError si la version chargée manque.
        config = self._config.get(workflow.workflow_name, workflow.version)

        # L'événement doit être accepté par cette configuration.
        if event.name not in config.declared_events:
            return None

        return config

    # ------------------------------------------------------------------
    # Création de nouveaux workflows
    # ------------------------------------------------------------------

    def _evaluate_new_workflows(
        self,
        event: IncomingEvent,
        existing_by_name: dict[str, list[RunContext]],
        workflows: list[Workflow],
    ) -> list[RunContext]:

        results: list[RunContext] = []

        for config in self._config.matching(event):

            if config.initializers.get(event.name) is None:
                continue

            dedup_hash = self._event_gate(config, event)

            # Rejeu (même Uuid) ou doublon fonctionnel (même empreinte) :
            # un événement déjà intégré par un workflow de cette
            # configuration ne doit pas en recréer un.
            if any(
                w.workflow_name == config.name
                and self._already_integrated(w, event, dedup_hash)
                for w in workflows
            ):
                continue

            ctx = self._evaluate_if_workflow_must_be_created(event, config)
            if ctx is None:
                continue
            ctx.event.dedup_hash = dedup_hash

            siblings = existing_by_name.get(ctx.workflow.workflow_name, [])
            last = max(siblings, key=lambda c: c.workflow.concurrency, default=None)

            if last is None:
                results.append(
                    self._execute_transition_after_creation(config, ctx)
                )

            # Garde CONCURENCY stricte (le source utilisait <=, autorisant
            # une instance de plus que la limite).
            elif last.workflow.concurrency < config.concurrency:
                ctx.workflow.concurrency = last.workflow.concurrency + 1
                results.append(
                    self._execute_transition_after_creation(config, ctx)
                )

        return results

    def _evaluate_if_workflow_must_be_created(
        self, event: IncomingEvent, config: WorkflowConfig
    ) -> RunContext | None:

        initializer = config.initializers.get(event.name)
        if initializer is None:
            return None

        workflow = self.factory.create_new_workflow(
            config.name,
            config.version,
            event.external_id,
            event.extended_datas,
        )

        ctx = self.factory.create_context(workflow, event)

        for switch in initializer.switchs:
            if self._evaluate(switch, ctx):
                ctx.event.to_state = ctx.event.from_state = switch.target_state_name
                ctx.workflow.recursive = initializer.recursive
                break

        if not ctx.event.from_state:
            return None

        return ctx

    def _execute_transition_after_creation(
        self, config: WorkflowConfig, ctx: RunContext
    ) -> RunContext:

        state = config.states[ctx.event.to_state]
        self._collect_rule_actions(state.incoming_rules, ctx)

        if ctx.workflow.recursive:
            self._evaluate_event_in_current_workflow(config, ctx)

        return ctx

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    def _evaluate_event_in_current_workflow(
        self, config: WorkflowConfig, ctx: RunContext
    ) -> None:

        state = config.states[ctx.event.from_state]

        incoming_event_config = state.events.get(ctx.incoming_event.name)
        if incoming_event_config is None:
            return

        # Actions attachées à l'arrivée de l'événement lui-même.
        self._collect_rule_actions(incoming_event_config.rules, ctx)

        for transition in incoming_event_config.transitions:
            if self._evaluate(transition, ctx):

                # Actions de la transition, puis sortie d'état.
                self._collect_rule_actions(transition.rule_actions, ctx)
                self._collect_rule_actions(state.outcoming_rules, ctx)

                state = transition.target_state
                ctx.event.to_state = state.name

                # Entrée dans le nouvel état.
                self._collect_rule_actions(state.incoming_rules, ctx)

                break

    def _collect_rule_actions(
        self, rules: list[ResultRuleConfig], ctx: RunContext
    ) -> None:
        for rule in rules:
            if self._evaluate(rule, ctx):
                for action in rule.actions:
                    ctx.actions.append(action.map(ctx))

    # ------------------------------------------------------------------
    # Évaluation des règles WHEN (trace de diagnostic sur le contexte)
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate(
        rule: TransitionConfig | InitializationConfig | ResultRuleConfig,
        ctx: RunContext,
    ) -> bool:
        if rule.when_rule is None:
            return True

        evaluation = ctx.current_evaluation
        evaluation.when_rule_text = rule.when_rule_text
        evaluation.when_rule_code = rule.when_rule_code
        evaluation.when_rule_position = rule.when_rule_position
        try:
            return bool(rule.when_rule(ctx))
        finally:
            evaluation.when_rule_text = ""
            evaluation.when_rule_code = ""
            evaluation.when_rule_position = RuleSpan.none()

    # ------------------------------------------------------------------
    # Traduction des actions collectées
    # ------------------------------------------------------------------

    def _translate_actions(self, contexts: list[RunContext]) -> None:
        for ctx in contexts:
            for action in ctx.actions:
                pushed = self.translator.translate(ctx, action)
                if action.event is not None:
                    action.event.actions.append(pushed)
