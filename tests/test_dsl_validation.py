"""Validation stricte à la construction : erreurs positionnées du visiteur.

Couvre aussi les bugs du source à ne pas reproduire (analyse §5) :
la condition inversée de ``VisitParameters`` sur les paramètres dupliqués,
et les arguments ``@…`` d'action qui devenaient des chaînes littérales.
"""

from __future__ import annotations

import pytest

from urban_workflow import FunctionRegistry
from urban_workflow.dsl import parse_config
from urban_workflow.exceptions import (
    DslSyntaxError,
    DuplicatedArgumentNameError,
    InvalidArgumentNameError,
    InvalidArgumentValueError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
    MissingStateError,
)


def make_rules() -> FunctionRegistry:
    rules = FunctionRegistry("rule")
    rules.add("IsMajor", lambda ctx, agemin: True)
    rules.add("IsEmpty", lambda ctx, text: not text)
    return rules


def parse(payload: str, filename: str = "test.wf"):
    return parse_config(payload, rules=make_rules(), filename=filename)


HEADER = """
    NAME wrk1
    DEFINE EVENT  Event1 'e1';
    DEFINE RULE   IsMajor (INTEGER agemin) 'r1';
    DEFINE ACTION Cut (TEXT key) 'a1';
"""


class TestSyntaxErrors:
    def test_syntax_error_is_positioned(self):
        with pytest.raises(DslSyntaxError) as excinfo:
            parse("NAME ... n'importe quoi")
        assert excinfo.value.errors
        error = excinfo.value.errors[0]
        assert error.line == 1
        assert error.filename == "test.wf"
        assert "test.wf:1:" in str(error)

    def test_missing_semicolon(self):
        payload = """
            NAME wrk1
            DEFINE EVENT Event1 'e1'
        """
        with pytest.raises(DslSyntaxError):
            parse(payload)


class TestActionValidation:
    def test_undeclared_action(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Unknown(key = 'v')
            ;
        """
        with pytest.raises(InvalidMethodReferenceError, match=r"Unknown.*not declared"):
            parse(payload)

    def test_unknown_argument_name(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Cut(wrong = 'v')
            ;
        """
        with pytest.raises(InvalidArgumentNameError, match="wrong"):
            parse(payload)

    def test_missing_argument(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Cut()
            ;
        """
        with pytest.raises(MissingArgumentNameError, match="key"):
            parse(payload)

    def test_duplicated_argument(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Cut(key = 'a', key = 'b')
            ;
        """
        with pytest.raises(DuplicatedArgumentNameError, match="key"):
            parse(payload)

    def test_error_message_is_positioned(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Unknown(key = 'v')
            ;
        """
        with pytest.raises(InvalidMethodReferenceError, match=r"test\.wf:\d+:\d+"):
            parse(payload)


class TestRuleValidation:
    def test_unregistered_rule(self):
        payload = HEADER + """
            INITIALIZE WORKFLOW
                ON EVENT Event1 WHEN NotRegistered() SWITCH State1
            DEFINE STATE State1 'state 1' ;
        """
        with pytest.raises(InvalidMethodReferenceError, match="NotRegistered"):
            parse(payload)

    def test_wrong_argument_name_against_callable(self):
        payload = HEADER + """
            INITIALIZE WORKFLOW
                ON EVENT Event1 WHEN IsMajor(wrong = '18') SWITCH State1
            DEFINE STATE State1 'state 1' ;
        """
        with pytest.raises(InvalidArgumentNameError, match="wrong"):
            parse(payload)

    def test_missing_argument_against_callable(self):
        payload = HEADER + """
            INITIALIZE WORKFLOW
                ON EVENT Event1 WHEN IsMajor() SWITCH State1
            DEFINE STATE State1 'state 1' ;
        """
        with pytest.raises(MissingArgumentNameError, match="agemin"):
            parse(payload)

    def test_bad_literal_for_declared_type(self):
        payload = HEADER + """
            INITIALIZE WORKFLOW
                ON EVENT Event1 WHEN IsMajor(agemin = 'pas un entier') SWITCH State1
            DEFINE STATE State1 'state 1' ;
        """
        with pytest.raises(InvalidArgumentValueError, match="pas un entier"):
            parse(payload)


class TestDuplicatedDeclarations:
    def test_duplicated_action(self):
        payload = """
            NAME wrk1
            DEFINE ACTION Cut (TEXT key) 'a1';
            DEFINE ACTION Cut (TEXT key) 'a2';
        """
        with pytest.raises(DuplicatedArgumentNameError, match="Cut"):
            parse(payload)

    def test_rule_and_action_share_namespace(self):
        payload = """
            NAME wrk1
            DEFINE RULE   Cut (TEXT key) 'r1';
            DEFINE ACTION Cut (TEXT key) 'a1';
        """
        with pytest.raises(DuplicatedArgumentNameError, match="already declared as a rule"):
            parse(payload)

    def test_duplicated_event(self):
        payload = """
            NAME wrk1
            DEFINE EVENT Event1 'e1';
            DEFINE EVENT Event1 'e2';
        """
        with pytest.raises(DuplicatedArgumentNameError, match="Event1"):
            parse(payload)

    def test_duplicated_constant(self):
        payload = """
            NAME wrk1
            DEFINE CONST agemin 18 'c1';
            DEFINE CONST agemin 21 'c2';
        """
        with pytest.raises(DuplicatedArgumentNameError, match="agemin"):
            parse(payload)

    def test_duplicated_parameter_raises(self):
        # Bug §5-like du source non reproduit : VisitParameters inversait la
        # condition et signalait les paramètres NON dupliqués.
        payload = """
            NAME wrk1
            DEFINE ACTION Cut (TEXT key, INTEGER key) 'a1';
        """
        with pytest.raises(DuplicatedArgumentNameError, match="parameter 'key'"):
            parse(payload)

    def test_duplicated_state(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1' ;
            DEFINE STATE State1 'state 1 bis' ;
        """
        with pytest.raises(DuplicatedArgumentNameError, match="State1"):
            parse(payload)

    def test_duplicated_event_in_state(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON EVENT Event1 SWITCH State2
                ON EVENT Event1 SWITCH State2
            ;
            DEFINE STATE State2 'state 2' ;
        """
        with pytest.raises(DuplicatedArgumentNameError, match="Event1"):
            parse(payload)


class TestSwitchTargets:
    def test_missing_transition_target(self):
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON EVENT Event1 SWITCH Nowhere
            ;
        """
        with pytest.raises(MissingStateError, match=r"test\.wf:\d+:\d+.*Nowhere"):
            parse(payload)

    def test_missing_initializer_target(self):
        payload = HEADER + """
            INITIALIZE WORKFLOW
                ON EVENT Event1 SWITCH Nowhere
        """
        with pytest.raises(MissingStateError, match="Nowhere"):
            parse(payload)


class TestArgumentInterpretation:
    def test_at_path_is_not_a_literal_string(self):
        # Bug du source non reproduit : GetLambda transformait les chemins
        # @… des actions en chaînes littérales.
        payload = HEADER + """
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Cut(key = @Event.Uuid)
            ;
        """
        config = parse(payload)
        argument = config.states["State1"].incoming_rules[0].actions[0].arguments["key"]
        from urban_workflow.values import ContextRef

        assert isinstance(argument, ContextRef)
        assert argument.path == "Event.Uuid"

    def test_bare_name_resolves_constant_then_literal(self):
        payload = """
            NAME wrk1
            DEFINE ACTION Tag (TEXT label, TEXT other) 'a1';
            DEFINE CONST  color 'blue' 'c1';
            DEFINE STATE State1 'state 1'
                ON ENTER STATE EXECUTE Tag(label = color, other = unknownword)
            ;
        """
        config = parse(payload)
        arguments = config.states["State1"].incoming_rules[0].actions[0].arguments
        assert arguments["label"] == "blue"  # constante résolue
        assert arguments["other"] == "unknownword"  # littéral tel quel

    def test_custom_kind_execute(self):
        payload = """
            NAME wrk1
            DEFINE ACTION Notify (TEXT target) 'a1';
            DEFINE STATE State1 'state 1'
                ON ENTER STATE mykind Notify(target = 'ops')
            ;
        """
        config = parse(payload)
        action = config.states["State1"].incoming_rules[0].actions[0]
        assert action.kind == "mykind"
        assert action.name == "Notify"
