"""Visiteur DSL → :class:`~urban_workflow.config.WorkflowConfig`.

Réécriture Python de ``WorkflowConfigVisitor`` (1 292 lignes C#) sur la base
``WorkflowParserVisitor`` générée par ANTLR. Différences assumées avec le
source (cf. ``docs/analyse-portage.md`` §6) :

- les conditions ``WHEN`` sont compilées en **composition de closures**
  (``lambda ctx: left(ctx) and right(ctx)``) au lieu d'arbres d'expressions ;
- les arguments ``@a.b.c`` deviennent des
  :class:`~urban_workflow.values.ContextRef` paresseuses ;
- la validation (déclarations, arguments nommés, états cibles des ``SWITCH``)
  lève des exceptions **positionnées** (fichier, ligne, colonne) au lieu
  d'accumuler silencieusement ;
- les bugs du source ne sont pas reproduits (condition inversée de
  ``VisitParameters`` sur les paramètres dupliqués, arguments ``@…``
  d'action transformés en chaînes littérales par ``GetLambda``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from antlr4.tree.Tree import ErrorNode

from .. import constants
from ..config import (
    DeclaredEventConfig,
    IncomingEventConfig,
    InitializationOnEventConfig,
    ResultActionConfig,
    ResultRuleConfig,
    StateConfig,
    TransitionConfig,
    WorkflowConfig,
)
from ..config.rules import Rule
from ..exceptions import (
    DslSyntaxError,
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
    MissingStateError,
    UnknownSchemaError,
    WorkflowError,
)
from ..models import RuleSpan, RunContext
from ..registry import FunctionRegistry
from ..schemas import SchemaRegistry
from ..values import ContextRef, ContextValue, resolve_value
from .errors import DslErrorModel
from .generated.WorkflowParser import WorkflowParser
from .generated.WorkflowParserVisitor import WorkflowParserVisitor
from .parser import _unquote

#: Types DSL (``TEXT | INTEGER | DECIMAL``) → types Python.
_DSL_TYPES: dict[str, type] = {"TEXT": str, "INTEGER": int, "DECIMAL": float}


@dataclass
class DeclaredFunction:
    """Signature déclarée par ``DEFINE RULE`` / ``DEFINE ACTION``."""

    name: str
    kind: str = "action"  # "rule" ou "action" (diagnostics)
    comment: str = ""
    parameters: dict[str, type] = field(default_factory=dict)


@dataclass
class ConstantModel:
    """Constante déclarée par ``DEFINE CONST``."""

    key: str
    value: Any = None
    comment: str = ""


def _log(ctx: RunContext, message: str) -> None:
    log = getattr(ctx, "functional_log", None)
    if log is not None:
        log.append(message)


def _format_kwargs(kwargs: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value!r}" for key, value in kwargs.items())


class WorkflowConfigVisitor(WorkflowParserVisitor):
    """Construit un :class:`WorkflowConfig` depuis l'arbre syntaxique du DSL.

    Usage type (reprend l'API fluide du source) ::

        visitor = (
            WorkflowConfigVisitor()
            .add_rule("IsMajor", is_major)
            .add_rule("IsEmpty", is_empty)
        )
        config = parser.visit(visitor)

    Un visiteur construit **un seul** workflow : les fragments inclus sont
    visités d'abord (ils alimentent déclarations et constantes), puis le
    script complet. Les règles ``WHEN`` sont liées aux callables
    ``(ctx, **kwargs) -> bool`` enregistrés dans ``rules``.
    """

    def __init__(
        self,
        rules: FunctionRegistry | None = None,
        filename: str = "",
        schemas: SchemaRegistry | None = None,
    ) -> None:
        self._rules = rules if rules is not None else FunctionRegistry("rule")
        #: Registre des schémas d'événements (chargé à l'initialisation du
        #: moteur). ``None`` = les références ``AS @…`` sont stockées sans
        #: résolution ni validation (mode permissif, ex. playground).
        self._schemas = schemas
        self.filename = filename
        self.crc = 0
        self.errors: list[DslErrorModel] = []

        self._workflow: WorkflowConfig | None = None
        self._constants: dict[str, ConstantModel] = {}
        #: Signatures déclarées — rules et actions partagent l'espace de noms,
        #: comme dans le source.
        self._declarations: dict[str, DeclaredFunction] = {}
        #: Cibles de ``SWITCH`` à valider une fois tous les états connus.
        self._pending_switch_targets: list[tuple[str, Any]] = []

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def add_rule(self, name: str, func: Callable[..., bool]) -> WorkflowConfigVisitor:
        """Enregistre une règle métier ``(ctx, **kwargs) -> bool`` (API fluide)."""
        self._rules.add(name, func)
        return self

    @property
    def rules(self) -> FunctionRegistry:
        return self._rules

    @property
    def constants(self) -> dict[str, ConstantModel]:
        return dict(self._constants)

    @property
    def declarations(self) -> dict[str, DeclaredFunction]:
        return dict(self._declarations)

    # ------------------------------------------------------------------
    # Entrée : script
    # ------------------------------------------------------------------

    def visit(self, tree):
        if isinstance(tree, WorkflowParser.ScriptContext):
            errors = self._collect_error_nodes(tree)
            if errors:
                self.errors.extend(errors)
                details = "; ".join(str(error) for error in errors)
                raise DslSyntaxError(
                    f"{len(errors)} syntax error(s) in workflow script: {details}",
                    errors=errors,
                )
        return super().visit(tree)

    def _collect_error_nodes(self, tree) -> list[DslErrorModel]:
        errors: list[DslErrorModel] = []

        def walk(node) -> None:
            if isinstance(node, ErrorNode):
                symbol = node.getSymbol()
                errors.append(
                    DslErrorModel(
                        message=(
                            f"failed to parse script at position {symbol.start}, "
                            f"line {symbol.line}, col {symbol.column} '{symbol.text}'"
                        ),
                        filename=self.filename,
                        line=symbol.line,
                        column=symbol.column,
                        start_index=symbol.start,
                        text=symbol.text or "",
                    )
                )
            for i in range(node.getChildCount()):
                walk(node.getChild(i))

        walk(tree)
        return errors

    def visitScript(self, ctx: WorkflowParser.ScriptContext):
        if self._workflow is None:
            self._workflow = WorkflowConfig()

        self.visitChildren(ctx)

        if ctx.script_full() is not None:
            self._workflow.crc = self.crc
            self._validate_switch_targets()
            self._workflow.build()

        return self._workflow

    def visitScript_fragment(self, ctx: WorkflowParser.Script_fragmentContext):
        if ctx.DESCRIPTION() is not None:
            self._workflow.label = self.visitComment(ctx.comment())

        for statement in ctx.define_referenciel_statement():
            self._register_declaration(
                self.visitDefine_referenciel_statement(statement), statement
            )


    def visitScript_full(self, ctx: WorkflowParser.Script_fullContext):
        workflow = self._workflow
        workflow.name = self.visitKey(ctx.key())

        workflow.version = (
            self.visitNumber(ctx.versionNumber) if ctx.VERSION() is not None else 1
        )

        concurency = ctx.concurency()
        workflow.concurrency = (
            self.visitConcurency(concurency) if concurency is not None else 1
        )

        if ctx.DESCRIPTION() is not None:
            workflow.label = self.visitComment(ctx.comment())

        if ctx.MATCHING() is not None:
            for key, value in self.visitMatchings(ctx.matchings()):
                workflow.add_filter(key, value)

        for statement in ctx.define_referenciel_statement():
            self._register_declaration(
                self.visitDefine_referenciel_statement(statement), statement
            )

        for statement in ctx.define_state_statement():
            state = self.visitDefine_state_statement(statement)
            if state.name in workflow.states:
                self._raise_positioned(
                    DuplicatedArgumentNameError,
                    statement,
                    f"state {state.name!r} is already defined",
                )
            workflow.add_state(state)

        initializing = ctx.initializing()
        if initializing is not None:
            for initializer in self.visitInitializing(initializing):
                if initializer.event_name in workflow.initializers:
                    self._raise_positioned(
                        DuplicatedArgumentNameError,
                        initializing,
                        f"initializer for event {initializer.event_name!r} "
                        "is already defined",
                    )
                workflow.add_initializer(initializer)


    def visitConcurency(self, ctx: WorkflowParser.ConcurencyContext) -> int:
        return self.visitNumber(ctx.number())

    # ------------------------------------------------------------------
    # Déclarations (DEFINE EVENT / RULE / ACTION / CONST)
    # ------------------------------------------------------------------

    def visitDefine_referenciel_statement(
        self, ctx: WorkflowParser.Define_referenciel_statementContext
    ):
        for getter in (
            ctx.event_declaration_statement,
            ctx.rule_declaration_statement,
            ctx.action_declaration_statement,
            ctx.constant_declaration,
        ):
            sub = getter()
            if sub is not None:
                return self.visit(sub)
        raise AssertionError("empty define_referenciel_statement")  # pragma: no cover

    def _register_declaration(self, declaration, ctx) -> None:
        if isinstance(declaration, ConstantModel):
            if declaration.key in self._constants:
                self._raise_positioned(
                    DuplicatedArgumentNameError,
                    ctx,
                    f"constant {declaration.key!r} is already declared",
                )
            self._constants[declaration.key] = declaration

        elif isinstance(declaration, DeclaredEventConfig):
            if declaration.name in self._workflow.declared_events:
                self._raise_positioned(
                    DuplicatedArgumentNameError,
                    ctx,
                    f"event {declaration.name!r} is already declared",
                )
            self._workflow.declared_events[declaration.name] = declaration

        elif isinstance(declaration, DeclaredFunction):
            pass  # déjà enregistrée par la visite de la déclaration

        else:  # pragma: no cover
            raise AssertionError(type(declaration).__name__)

    def visitConstant_declaration(
        self, ctx: WorkflowParser.Constant_declarationContext
    ) -> ConstantModel:
        return ConstantModel(
            key=self.visitKey(ctx.key()),
            value=self.visitValue(ctx.value()),
            comment=self._optional_comment(ctx),
        )

    def visitValue(self, ctx: WorkflowParser.ValueContext):
        if ctx.string() is not None:
            return self.visitString(ctx.string())
        if ctx.number() is not None:
            return self.visitNumber(ctx.number())
        if ctx.delay() is not None:
            return self.visitDelay(ctx.delay())
        return ctx.getText()  # REGULAR_ID

    def visitEvent_declaration_statement(
        self, ctx: WorkflowParser.Event_declaration_statementContext
    ) -> DeclaredEventConfig:
        declared = DeclaredEventConfig(
            name=self.visitKey(ctx.key()),
            label=self._optional_comment(ctx),
        )

        # Extension urban-workflow : DEFINE EVENT … AS @schema
        if ctx.AS() is not None:
            declared.schema_ref = self.visitCompositekey(ctx.schemaRef).lstrip("@")
            if self._schemas is not None:
                try:
                    declared.schema = self._schemas.get(declared.schema_ref)
                except UnknownSchemaError as exc:
                    self._raise_positioned(UnknownSchemaError, ctx, str(exc))
                declared.dedup_keys = self._schemas.dedup_keys(declared.schema_ref)

        return declared

    def visitAction_declaration_statement(
        self, ctx: WorkflowParser.Action_declaration_statementContext
    ) -> DeclaredFunction:
        return self._declare_function(ctx, kind="action")

    def visitRule_declaration_statement(
        self, ctx: WorkflowParser.Rule_declaration_statementContext
    ) -> DeclaredFunction:
        return self._declare_function(ctx, kind="rule")

    def _declare_function(self, ctx, kind: str) -> DeclaredFunction:
        name = self.visitKey(ctx.key())

        if name in self._declarations:
            previous = self._declarations[name]
            self._raise_positioned(
                DuplicatedArgumentNameError,
                ctx,
                f"{kind} {name!r} is already declared as a {previous.kind}",
            )

        declaration = DeclaredFunction(
            name=name,
            kind=kind,
            comment=self._optional_comment(ctx),
        )

        parameters = ctx.parameters()
        if parameters is not None:
            declaration.parameters.update(self.visitParameters(parameters))

        self._declarations[name] = declaration
        return declaration

    def visitParameters(self, ctx: WorkflowParser.ParametersContext) -> dict[str, type]:
        result: dict[str, type] = {}
        for parameter in ctx.parameter():
            param_type, param_name = self.visitParameter(parameter)
            if param_name in result:
                # Le source inversait la condition (bug §5-like) : ici on
                # lève bien sur le doublon, avec la position.
                self._raise_positioned(
                    DuplicatedArgumentNameError,
                    parameter,
                    f"duplicated parameter {param_name!r}",
                )
            result[param_name] = param_type
        return result

    def visitParameter(self, ctx: WorkflowParser.ParameterContext) -> tuple[type, str]:
        return self.visitType(ctx.type_()), self.visitKey(ctx.key())

    def visitType(self, ctx: WorkflowParser.TypeContext) -> type:
        return _DSL_TYPES.get(ctx.getText(), object)

    # ------------------------------------------------------------------
    # États
    # ------------------------------------------------------------------

    def visitDefine_state_statement(
        self, ctx: WorkflowParser.Define_state_statementContext
    ) -> StateConfig:
        return self.visitState(ctx.state_())

    def visitState(self, ctx: WorkflowParser.StateContext) -> StateConfig:
        state = StateConfig(
            name=self.visitKey(ctx.key()),
            label=self._optional_comment(ctx),
        )

        for execute in ctx.execute():
            on_enter, on_exit, rule = self.visitExecute(execute)
            if on_enter:
                state.incoming_rules.append(rule)
            if on_exit:
                state.outcoming_rules.append(rule)

        for statement in ctx.on_event_statement():
            incoming_event, rule_pairs = self.visitOn_event_statement(statement)
            if incoming_event.name in state.events:
                self._raise_positioned(
                    DuplicatedArgumentNameError,
                    statement,
                    f"event {incoming_event.name!r} is already handled "
                    f"in state {state.name!r}",
                )
            state.events[incoming_event.name] = incoming_event

            for where, rule in rule_pairs:
                if where == "in":
                    state.incoming_rules.append(rule)
                elif where == "out":
                    state.outcoming_rules.append(rule)

        return state

    # ------------------------------------------------------------------
    # Initialisation (INITIALIZE WORKFLOW)
    # ------------------------------------------------------------------

    def visitInitializing(
        self, ctx: WorkflowParser.InitializingContext
    ) -> list[InitializationOnEventConfig]:
        return [self.visitInitializing_item(item) for item in ctx.initializing_item()]

    def visitInitializing_item(
        self, ctx: WorkflowParser.Initializing_itemContext
    ) -> InitializationOnEventConfig:
        event_name = self.visitKey(ctx.key(0))
        target_state_name = self.visitKey(ctx.key(1))
        self._pending_switch_targets.append((target_state_name, ctx.key(1)))

        when_rule: Rule | None = None
        when_rule_text = ""
        when_rule_code = ""
        when_rule_position: RuleSpan | None = None
        if ctx.WHEN() is not None:
            condition = ctx.rule_conditions()
            when_rule, when_rule_code = self.visitRule_conditions(condition)
            when_rule_text = self._source_text(condition)
            when_rule_position = self._span(condition)

        return InitializationOnEventConfig(
            event_name=event_name,
            recursive=ctx.RECURSIVE() is not None,
        ).add_switch(
            target_state_name,
            when_rule,
            when_rule_text,
            when_rule_code,
            when_rule_position,
        )

    # ------------------------------------------------------------------
    # Événements d'un état (ON EVENT / EXPIRE AFTER)
    # ------------------------------------------------------------------

    def visitOn_event_statement(
        self, ctx: WorkflowParser.On_event_statementContext
    ) -> tuple[IncomingEventConfig, list[tuple[str, ResultRuleConfig]]]:
        rule_pairs: list[tuple[str, ResultRuleConfig]] = []
        expire_rule: Rule | None = None
        expire_rule_text = ""

        incoming_event = IncomingEventConfig()

        key = ctx.key()
        if key is not None:
            incoming_event.name = self.visitKey(key)

        if ctx.EXPIRE() is not None:
            incoming_event.name = constants.EXPIRED_EVENT_NAME
            delay = self.visitDelay(ctx.delay())
            expire_rule = _expire_when_rule
            expire_rule_text = "@IncomingEvent.CurrentState == @Workflow.CurrentState"
            rule_pairs.extend(_expiration_rule_pairs(delay))

        for switch_state in ctx.switch_state():
            transition = self.visitSwitch_state(switch_state)
            if expire_rule is not None:
                _merge_when_rule(transition, expire_rule, expire_rule_text)
            incoming_event.add_transition(transition)

        return incoming_event, rule_pairs

    def visitSwitch_state(
        self, ctx: WorkflowParser.Switch_stateContext
    ) -> TransitionConfig:
        transition = TransitionConfig()

        if ctx.WHEN() is not None:
            condition = ctx.rule_conditions()
            transition.when_rule, transition.when_rule_code = self.visitRule_conditions(
                condition
            )
            transition.when_rule_text = self._source_text(condition)
            transition.when_rule_position = self._span(condition)

        for execute in ctx.execute2():
            transition.rule_actions.append(self.visitExecute2(execute))

        if ctx.SWITCH() is not None:
            transition.target_state_name = self.visitKey(ctx.key())
            self._pending_switch_targets.append(
                (transition.target_state_name, ctx.key())
            )

        return transition

    # ------------------------------------------------------------------
    # Exécution d'actions (ON ENTER/EXIT, EXECUTE, STORE)
    # ------------------------------------------------------------------

    def visitExecute(
        self, ctx: WorkflowParser.ExecuteContext
    ) -> tuple[bool, bool, ResultRuleConfig]:
        on_enter = ctx.ENTER() is not None
        on_exit = ctx.EXIT() is not None
        rule = self.visitExecute2(ctx.execute2())
        return on_enter, on_exit, rule

    def visitExecute2(self, ctx: WorkflowParser.Execute2Context) -> ResultRuleConfig:
        rule = ResultRuleConfig()

        delay = 0
        if ctx.WAITING() is not None:
            delay = self.visitDelay(ctx.delay())

        if ctx.WHEN() is not None:
            condition = ctx.rule_conditions()
            rule.when_rule, rule.when_rule_code = self.visitRule_conditions(condition)
            rule.when_rule_text = self._source_text(condition)
            rule.when_rule_position = self._span(condition)

        for execute3 in ctx.execute3():
            for action in self.visitExecute3(execute3):
                action.delay = delay
                rule.actions.append(action)

        return rule

    def visitExecute3(
        self, ctx: WorkflowParser.Execute3Context
    ) -> list[ResultActionConfig]:
        actions: list[ResultActionConfig] = []

        if ctx.STORE() is not None:
            for matchings in ctx.matchings():
                for key, value in self.visitMatchings(matchings):
                    actions.append(
                        ResultActionConfig(
                            name=f"update {key}",
                            label=f"update {key} to {value}",
                            kind=constants.SET_VALUE_ACTION_NAME,
                            arguments={"key": key, "value": value},
                        )
                    )
            return actions

        kind = (
            constants.PUSH_ACTION_NAME
            if ctx.EXECUTE() is not None
            else self.visitKey(ctx.key())
        )

        for action_ctx in ctx.action():
            action = self.visitAction(action_ctx)
            action.kind = kind
            actions.append(action)

        return actions

    def visitAction(self, ctx: WorkflowParser.ActionContext) -> ResultActionConfig:
        name = self.visitKey(ctx.key())

        declaration = self._declarations.get(name)
        if declaration is None:
            self._raise_positioned(
                InvalidMethodReferenceError,
                ctx,
                f"action {name!r} is not declared (DEFINE ACTION)",
            )

        action = ResultActionConfig(name=name)

        remaining = dict(declaration.parameters)
        arguments = ctx.arguments()
        if arguments is not None:
            for key, raw_value, argument_ctx in self.visitArguments(arguments):
                if key in action.arguments:
                    self._raise_positioned(
                        DuplicatedArgumentNameError,
                        argument_ctx,
                        f"duplicated argument {key!r} in call to action {name!r}",
                    )
                if key not in declaration.parameters:
                    self._raise_positioned(
                        InvalidArgumentNameError,
                        argument_ctx,
                        f"unknown argument {key!r} in call to action {name!r}; "
                        f"expected: {sorted(declaration.parameters)}",
                    )
                action.arguments[key] = self._make_argument_value(
                    raw_value, declaration.parameters[key], argument_ctx
                )
                remaining.pop(key, None)

        if remaining:
            self._raise_positioned(
                MissingArgumentNameError,
                ctx,
                f"missing argument(s) {sorted(remaining)} in call to action {name!r}",
            )

        return action

    # ------------------------------------------------------------------
    # Arguments
    # ------------------------------------------------------------------

    def visitArguments(
        self, ctx: WorkflowParser.ArgumentsContext
    ) -> list[tuple[str, str, Any]]:
        """Retourne ``[(nom, valeur brute, contexte ANTLR), …]``."""
        return [self.visitArgument(argument) for argument in ctx.argument()]

    def visitArgument(self, ctx: WorkflowParser.ArgumentContext) -> tuple[str, str, Any]:
        key = self.visitKey(ctx.key())
        value = self.visitArgumentValue(ctx.argumentValue())
        return key, value, ctx

    def visitArgumentValue(self, ctx: WorkflowParser.ArgumentValueContext) -> str:
        """Valeur brute, telle qu'écrite : ``'texte'`` (quotes incluses),
        ``@chemin.composé`` ou identifiant/chemin nu."""
        composite = ctx.compositekey()
        if composite is not None:
            return self.visitCompositekey(composite)
        return ctx.string().getText()

    def _make_argument_value(
        self, raw: str, declared_type: type | None, ctx
    ) -> ContextValue:
        """Interprète une valeur brute d'argument.

        - ``'…'``  → littéral converti vers le type déclaré ;
        - ``@a.b`` → :class:`ContextRef` (résolution paresseuse) ;
        - nom nu   → constante ``DEFINE CONST`` si elle existe, sinon littéral.
        """
        if raw.startswith("'") and raw.endswith("'"):
            return self._convert(_unquote(raw), declared_type, ctx)

        if raw.startswith("@"):
            return ContextRef.parse(raw)

        constant = self._constants.get(raw)
        if constant is not None:
            return self._convert(constant.value, declared_type, ctx)

        return self._convert(raw, declared_type, ctx)

    def _convert(self, value: Any, declared_type: type | None, ctx) -> Any:
        if declared_type is None or declared_type is object:
            return value
        if isinstance(value, declared_type):
            return value
        try:
            return declared_type(value)
        except (TypeError, ValueError):
            self._raise_positioned(
                InvalidArgumentValueError,
                ctx,
                f"cannot convert {value!r} to {declared_type.__name__}",
            )

    # ------------------------------------------------------------------
    # Conditions WHEN → closures
    # ------------------------------------------------------------------

    def visitRule_conditions(
        self, ctx: WorkflowParser.Rule_conditionsContext
    ) -> tuple[Rule, str]:
        """Compile récursivement une condition en ``(closure, code lisible)``."""

        key = ctx.key()
        if key is not None:
            return self._compile_rule_call(ctx, self.visitKey(key))

        if ctx.NOT() is not None:
            inner, inner_code = self.visitRule_conditions(ctx.rule_conditions(0))

            def negate(run_ctx: RunContext, _inner: Rule = inner) -> bool:
                result = not _inner(run_ctx)
                _log(run_ctx, f"NOT -> {result}")
                return result

            return negate, f"NOT {inner_code}"

        if ctx.AND() is not None:
            left, left_code = self.visitRule_conditions(ctx.rule_conditions(0))
            right, right_code = self.visitRule_conditions(ctx.rule_conditions(1))

            def conjunction(
                run_ctx: RunContext, _left: Rule = left, _right: Rule = right
            ) -> bool:
                result = _left(run_ctx) and _right(run_ctx)
                _log(run_ctx, f"AND -> {result}")
                return result

            return conjunction, f"({left_code} AND {right_code})"

        if ctx.OR() is not None:
            left, left_code = self.visitRule_conditions(ctx.rule_conditions(0))
            right, right_code = self.visitRule_conditions(ctx.rule_conditions(1))

            def disjunction(
                run_ctx: RunContext, _left: Rule = left, _right: Rule = right
            ) -> bool:
                result = _left(run_ctx) or _right(run_ctx)
                _log(run_ctx, f"OR -> {result}")
                return result

            return disjunction, f"({left_code} OR {right_code})"

        # LEFT_PAREN rule_conditions RIGHT_PAREN
        inner, inner_code = self.visitRule_conditions(ctx.rule_conditions(0))
        return inner, f"({inner_code})"

    def _compile_rule_call(self, ctx, name: str) -> tuple[Rule, str]:
        if name not in self._rules:
            self._raise_positioned(
                InvalidMethodReferenceError,
                ctx,
                f"rule {name!r} is not registered",
            )
        func = self._rules.get(name)

        provided: list[tuple[str, str, Any]] = []
        arguments = ctx.arguments()
        if arguments is not None:
            provided = self.visitArguments(arguments)

        # Validation contre la signature du callable enregistré.
        try:
            self._rules.validate_call(name, [key for key, _, _ in provided])
        except WorkflowError as exc:
            self._raise_positioned(type(exc), ctx, str(exc))

        declaration = self._declarations.get(name)
        resolvers: dict[str, ContextValue] = {}
        for key, raw_value, argument_ctx in provided:
            declared_type = (
                declaration.parameters.get(key) if declaration is not None else None
            )
            if declaration is not None and key not in declaration.parameters:
                self._raise_positioned(
                    InvalidArgumentNameError,
                    argument_ctx,
                    f"unknown argument {key!r} in call to rule {name!r}; "
                    f"declared: {sorted(declaration.parameters)}",
                )
            resolvers[key] = self._make_argument_value(
                raw_value, declared_type, argument_ctx
            )

        code = f"{name}({', '.join(f'{k}={raw}' for k, raw, _ in provided)})"

        def call_rule(
            run_ctx: RunContext,
            _func: Callable[..., bool] = func,
            _name: str = name,
            _resolvers: dict[str, ContextValue] = resolvers,
        ) -> bool:
            kwargs = {
                key: resolve_value(value, run_ctx) for key, value in _resolvers.items()
            }
            try:
                result = bool(_func(run_ctx, **kwargs))
            except Exception as exc:
                _log(run_ctx, f"{_name}({_format_kwargs(kwargs)}) !! {exc!r}")
                raise
            _log(run_ctx, f"{_name}({_format_kwargs(kwargs)}) -> {result}")
            return result

        return call_rule, code

    # ------------------------------------------------------------------
    # Feuilles
    # ------------------------------------------------------------------

    def visitMatchings(
        self, ctx: WorkflowParser.MatchingsContext
    ) -> list[tuple[str, str]]:
        return [self.visitMatching(matching) for matching in ctx.matching()]

    def visitMatching(self, ctx: WorkflowParser.MatchingContext) -> tuple[str, str]:
        return self.visitKey(ctx.key()), self.visitString(ctx.string())

    def visitKey(self, ctx: WorkflowParser.KeyContext) -> str:
        return ctx.getText()

    def visitCompositekey(self, ctx: WorkflowParser.CompositekeyContext) -> str:
        return ctx.getText()

    def visitComment(self, ctx: WorkflowParser.CommentContext) -> str:
        return _unquote(ctx.getText())

    def visitString(self, ctx: WorkflowParser.StringContext) -> str:
        return _unquote(ctx.getText())

    def visitNumber(self, ctx: WorkflowParser.NumberContext) -> int:
        return int(ctx.getText())

    def visitNumeric(self, ctx: WorkflowParser.NumericContext) -> float:
        numbers = ctx.number()
        return float(f"{numbers[0].getText()}.{numbers[1].getText()}")

    def visitDelay(self, ctx: WorkflowParser.DelayContext) -> int:
        """Délai en **minutes** (comme dans le source)."""
        result = self.visitNumber(ctx.number())
        if ctx.HOUR() is not None:
            result *= 60
        elif ctx.DAY() is not None:
            result *= 60 * 24
        return result

    # ------------------------------------------------------------------
    # Aides internes
    # ------------------------------------------------------------------

    def _optional_comment(self, ctx) -> str:
        comment = ctx.comment()
        return self.visitComment(comment) if comment is not None else ""

    def _validate_switch_targets(self) -> None:
        for target_name, ctx in self._pending_switch_targets:
            if target_name not in self._workflow.states:
                self._raise_positioned(
                    MissingStateError,
                    ctx,
                    f"missing state name {target_name}",
                )
        self._pending_switch_targets.clear()

    def _position(self, ctx) -> str:
        token = ctx.start if hasattr(ctx, "start") else ctx
        prefix = f"{self.filename}:" if self.filename else ""
        return f"{prefix}{token.line}:{token.column}"

    def _raise_positioned(self, exc_type: type[WorkflowError], ctx, message: str):
        raise exc_type(f"{self._position(ctx)}: {message}")

    def _span(self, ctx) -> RuleSpan:
        return RuleSpan(
            start_line=ctx.start.line,
            start_column=ctx.start.column,
            start_index=ctx.start.start,
            stop_line=ctx.stop.line,
            stop_column=ctx.stop.column,
            stop_index=ctx.stop.stop,
        )

    @staticmethod
    def _source_text(ctx) -> str:
        """Texte source original de la règle (espacement préservé)."""
        stream = ctx.start.getInputStream()
        return stream.getText(ctx.start.start, ctx.stop.stop)


# ----------------------------------------------------------------------
# EXPIRE AFTER — règles et actions techniques
# ----------------------------------------------------------------------


def _expire_when_rule(run_ctx: RunContext) -> bool:
    """L'événement ``__expired`` ne vaut que si l'état n'a pas changé depuis."""
    value = run_ctx.incoming_event.extended_datas.get("CurrentState")
    if value is None:
        return False
    return run_ctx.workflow.current_state == str(value)


def _cancel_reminder_when_rule(run_ctx: RunContext) -> bool:
    return run_ctx.incoming_event.name != constants.EXPIRED_EVENT_NAME


def _expiration_rule_pairs(delay: int) -> list[tuple[str, ResultRuleConfig]]:
    """Actions techniques d'un ``EXPIRE AFTER`` (cf. ``AddExpirationActions``).

    - à l'entrée de l'état : pousser le rappel différé ``__expired`` ;
    - à la sortie : annuler le rappel, sauf si on sort à cause de
      l'expiration elle-même.
    """
    push_reminder = ResultRuleConfig()
    push_reminder.actions.append(
        ResultActionConfig(
            name=constants.EXPIRED_EVENT_NAME,
            label="Expiration",
            delay=delay,
            kind=constants.PUSH_ACTION_NAME,
        )
    )

    cancel_reminder = ResultRuleConfig(
        when_rule=_cancel_reminder_when_rule,
        when_rule_text=f"@IncomingEvent.Name != '{constants.EXPIRED_EVENT_NAME}'",
    )
    cancel_reminder.actions.append(
        ResultActionConfig(
            name=constants.CANCEL_REMINDER_ACTION,
            label="Cancel Expiration",
            kind=constants.PUSH_ACTION_NAME,
        )
    )

    return [("in", push_reminder), ("out", cancel_reminder)]


def _merge_when_rule(
    transition: TransitionConfig, guard: Rule, guard_text: str
) -> None:
    """Combine la garde d'expiration avec la règle propre de la transition."""
    if transition.when_rule is None:
        transition.when_rule = guard
        transition.when_rule_text = guard_text
    else:
        own_rule = transition.when_rule

        def combined(run_ctx: RunContext, _guard: Rule = guard, _own: Rule = own_rule) -> bool:
            return _guard(run_ctx) and _own(run_ctx)

        transition.when_rule = combined
        transition.when_rule_text = f"{guard_text} AND {transition.when_rule_text}"
