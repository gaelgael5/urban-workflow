"""Tests golden du DSL — port de ``ParserUnitTest.cs`` (TestUnserializeConfig).

Le script complet du test source doit produire une configuration
équivalente : mêmes états, transitions, règles, actions, positions.
"""

from __future__ import annotations

from urban_workflow import (
    Event,
    IncomingEvent,
    RunContext,
    Workflow,
    constants,
)
from urban_workflow.dsl import parse_config
from urban_workflow.values import ContextRef

# Script du test source (ParserUnitTest.payload), repris tel quel.
PAYLOAD = """
    NAME wrk1 VERSION 2
    CONCURENCY 1
    DESCRIPTION                 'workflow de test'
    MATCHING (Country = 'France')

    DEFINE EVENT     Event1                     'incoming event 1';
    DEFINE EVENT     Event2                     'incoming event 2';

    DEFINE RULE      IsMajor (INTEGER agemin)   'this method 1';
    DEFINE RULE      IsEmpty (TEXT text)        'this method 2';

    DEFINE ACTION    Cut(TEXT key)              'Remove user';

    DEFINE CONST     Name 'gael'                'ben oui c est moi';
    DEFINE CONST     agemin 18                  'min for been major';

    INITIALIZE WORKFLOW
        ON EVENT Event1 WHEN NOT IsEmpty(text = @Workflow.ExternalId)
            SWITCH State1

    DEFINE STATE State1                         'state 1'
        ON ENTER STATE
            WHEN IsMajor(agemin = agemin)
                EXECUTE Cut(key = @Workflow.ExternalId)
                     -- Cut(key = @Workflow.ExternalId)
                STORE   (Status = 'InProgress')
                     -- (Status = 'InProgress')

        ON EVENT Event2
            SWITCH State2

        EXPIRE AFTER 2 DAY
            SWITCH State3

    ;

    DEFINE STATE State2            'state 2'

    ;

    DEFINE STATE State3            'state 3'

    ;
"""

# Variante avec RECURSIVE et condition parenthésée (ParserUnitTest.payload2).
PAYLOAD2 = PAYLOAD.replace(
    "ON EVENT Event1 WHEN NOT IsEmpty(text = @Workflow.ExternalId)\n"
    "            SWITCH State1",
    "ON EVENT Event1 WHEN (NOT IsEmpty(text = @Workflow.ExternalId))\n"
    "            RECURSIVE SWITCH State1",
)


def is_major(ctx: RunContext, agemin: int) -> bool:
    age = ctx.incoming_event.extended_datas.get("Age")
    if age is None:
        return False
    return int(age) >= agemin


def is_empty(ctx: RunContext, text: str) -> bool:
    return not text


def get_config(payload: str = PAYLOAD, filename: str = "memory text"):
    from urban_workflow import FunctionRegistry

    rules = FunctionRegistry("rule")
    rules.add("IsMajor", is_major)
    rules.add("IsEmpty", is_empty)
    return parse_config(payload, rules=rules, filename=filename)


def make_context(
    external_id: str = "ext-1",
    current_state: str = "",
    incoming_name: str = "Event1",
    **extended,
) -> RunContext:
    workflow = Workflow(workflow_name="wrk1", version=2, external_id=external_id)
    if current_state:
        workflow.events.append(Event(name="init", to_state=current_state))
    incoming = IncomingEvent(name=incoming_name, extended_datas=dict(extended))
    return RunContext(workflow=workflow, incoming_event=incoming)


# ----------------------------------------------------------------------
# Golden : structure de la configuration (port de TestUnserializeConfig)
# ----------------------------------------------------------------------


class TestUnserializeConfig:
    def test_header(self):
        config = get_config()
        assert config.name == "wrk1"
        assert config.version == 2
        assert config.concurrency == 1
        assert config.label == "workflow de test"
        assert config.filters == {"Country": "France"}

    def test_declared_events(self):
        config = get_config()
        # Event1, Event2 (déclarés) + $_result, __expired (techniques).
        assert len(config.declared_events) == 4
        assert set(config.declared_events) == {
            "Event1",
            "Event2",
            constants.RESULT_ACTION_NAME,
            constants.EXPIRED_EVENT_NAME,
        }
        assert config.declared_events["Event1"].label == "incoming event 1"

    def test_initializers(self):
        config = get_config()
        assert len(config.initializers) == 1
        initializer = config.initializers["Event1"]
        assert initializer.recursive is False
        assert len(initializer.switchs) == 1
        switch = initializer.switchs[0]
        assert switch.target_state_name == "State1"
        assert switch.target_state is config.states["State1"]
        assert switch.when_rule is not None

    def test_states_and_transitions(self):
        config = get_config()
        assert len(config.states) == 3

        s1 = config.states["State1"]
        s2 = config.states["State2"]
        s3 = config.states["State3"]

        assert len(s1.events) == 2

        event2 = s1.events["Event2"]
        assert len(event2.transitions) == 1
        assert event2.transitions[0].target_state_name == "State2"
        assert event2.transitions[0].target_state is s2

        expired = s1.events[constants.EXPIRED_EVENT_NAME]
        assert len(expired.transitions) == 1
        assert expired.transitions[0].target_state is s3

    def test_incoming_and_outcoming_rules(self):
        config = get_config()
        s1 = config.states["State1"]

        # ON ENTER (when IsMajor) + action d'expiration à l'entrée.
        assert len(s1.incoming_rules) == 2
        enter = s1.incoming_rules[0]
        assert enter.when_rule is not None
        assert len(enter.actions) == 2
        assert enter.actions[0].kind == "$_push"
        assert enter.actions[0].name == "Cut"
        assert enter.actions[1].kind == "$_update"
        assert enter.actions[1].name == "update Status"

        # Annulation du rappel à la sortie.
        assert len(s1.outcoming_rules) == 1
        out = s1.outcoming_rules[0]
        assert out.when_rule is not None
        assert len(out.actions) == 1
        assert out.actions[0].kind == "$_push"
        assert out.actions[0].name == constants.CANCEL_REMINDER_ACTION

    def test_expiration_action_delay_in_minutes(self):
        config = get_config()
        s1 = config.states["State1"]
        reminder = s1.incoming_rules[1].actions[0]
        assert reminder.name == constants.EXPIRED_EVENT_NAME
        assert reminder.kind == constants.PUSH_ACTION_NAME
        assert reminder.delay == 2 * 24 * 60  # 2 DAY → minutes

    def test_store_arguments(self):
        config = get_config()
        store = config.states["State1"].incoming_rules[0].actions[1]
        assert store.arguments == {"key": "Status", "value": "InProgress"}
        assert store.label == "update Status to InProgress"

    def test_action_argument_is_context_ref(self):
        config = get_config()
        cut = config.states["State1"].incoming_rules[0].actions[0]
        assert isinstance(cut.arguments["key"], ContextRef)
        assert cut.arguments["key"].path == "Workflow.ExternalId"

        ctx = make_context(external_id="ABC")
        assert cut.arguments["key"](ctx) == "ABC"


class TestPayload2:
    def test_recursive_and_parenthesized_condition(self):
        config = get_config(PAYLOAD2)
        initializer = config.initializers["Event1"]
        assert initializer.recursive is True

        switch = initializer.switchs[0]
        assert switch.when_rule is not None
        assert switch.when_rule(make_context(external_id="x")) is True
        assert switch.when_rule(make_context(external_id="")) is False


# ----------------------------------------------------------------------
# Comportement des closures WHEN
# ----------------------------------------------------------------------


class TestWhenRules:
    def test_initializer_rule_not_is_empty(self):
        config = get_config()
        when = config.initializers["Event1"].switchs[0].when_rule
        assert when(make_context(external_id="something")) is True
        assert when(make_context(external_id="")) is False

    def test_enter_rule_is_major_uses_constant(self):
        config = get_config()
        when = config.states["State1"].incoming_rules[0].when_rule
        assert when(make_context(Age=25)) is True
        assert when(make_context(Age=17)) is False
        assert when(make_context()) is False  # Age absent

    def test_expire_transition_guard(self):
        config = get_config()
        expired = config.states["State1"].events[constants.EXPIRED_EVENT_NAME]
        when = expired.transitions[0].when_rule
        assert when is not None

        ctx = make_context(
            current_state="State1",
            incoming_name=constants.EXPIRED_EVENT_NAME,
            CurrentState="State1",
        )
        assert when(ctx) is True

        ctx = make_context(
            current_state="State2",
            incoming_name=constants.EXPIRED_EVENT_NAME,
            CurrentState="State1",
        )
        assert when(ctx) is False

        # pas de CurrentState dans l'événement → False
        ctx = make_context(
            current_state="State1", incoming_name=constants.EXPIRED_EVENT_NAME
        )
        assert when(ctx) is False

    def test_cancel_reminder_rule(self):
        config = get_config()
        out = config.states["State1"].outcoming_rules[0]
        assert out.when_rule(make_context(incoming_name="Event2")) is True
        assert (
            out.when_rule(make_context(incoming_name=constants.EXPIRED_EVENT_NAME))
            is False
        )
        assert (
            out.when_rule_text
            == f"@IncomingEvent.Name != '{constants.EXPIRED_EVENT_NAME}'"
        )

    def test_functional_log_records_evaluations(self):
        config = get_config()
        when = config.states["State1"].incoming_rules[0].when_rule
        ctx = make_context(Age=25)
        when(ctx)
        assert ctx.functional_log == ["IsMajor(agemin=18) -> True"]


# ----------------------------------------------------------------------
# Diagnostics : texte, code et position des règles
# ----------------------------------------------------------------------


class TestDiagnostics:
    def test_when_rule_text_is_source_slice(self):
        config = get_config()
        when_text = config.initializers["Event1"].switchs[0].when_rule_text
        assert when_text == "NOT IsEmpty(text = @Workflow.ExternalId)"

    def test_when_rule_code(self):
        config = get_config()
        assert (
            config.initializers["Event1"].switchs[0].when_rule_code
            == "NOT IsEmpty(text=@Workflow.ExternalId)"
        )
        assert (
            config.states["State1"].incoming_rules[0].when_rule_code
            == "IsMajor(agemin=agemin)"
        )

    def test_when_rule_position(self):
        config = get_config()
        span = config.initializers["Event1"].switchs[0].when_rule_position
        # La condition est sur la ligne "ON EVENT Event1 WHEN NOT IsEmpty…".
        line = next(
            index + 1
            for index, text in enumerate(PAYLOAD.splitlines())
            if "WHEN NOT IsEmpty" in text
        )
        assert span.start_line == line
        assert span.stop_line == line
        assert span.start_column == PAYLOAD.splitlines()[line - 1].index("NOT")
        assert span.stop_index > span.start_index


# ----------------------------------------------------------------------
# Conditions composées
# ----------------------------------------------------------------------


COMPOSED = """
    NAME wrk2
    DEFINE EVENT Event1 'e1';
    DEFINE RULE  IsMajor (INTEGER agemin) 'r1';
    DEFINE RULE  IsEmpty (TEXT text) 'r2';
    INITIALIZE WORKFLOW
        ON EVENT Event1
            WHEN IsMajor(agemin = '18') AND NOT IsEmpty(text = @Workflow.ExternalId)
                SWITCH State1
        ON EVENT Event2
            WHEN IsMajor(agemin = '21') OR IsEmpty(text = @Workflow.ExternalId)
                SWITCH State1
    DEFINE STATE State1 'state 1' ;
"""


class TestComposedConditions:
    def test_and_or_not(self):
        config = get_config(COMPOSED)
        assert config.version == 1  # VERSION absent → 1
        assert config.concurrency == 1  # CONCURENCY absent → 1

        on_e1 = config.initializers["Event1"].switchs[0].when_rule
        assert on_e1(make_context(external_id="x", Age=20)) is True
        assert on_e1(make_context(external_id="", Age=20)) is False
        assert on_e1(make_context(external_id="x", Age=15)) is False

        on_e2 = config.initializers["Event2"].switchs[0].when_rule
        assert on_e2(make_context(external_id="x", Age=22)) is True
        assert on_e2(make_context(external_id="", Age=15)) is True
        assert on_e2(make_context(external_id="x", Age=15)) is False

    def test_composed_code(self):
        config = get_config(COMPOSED)
        assert (
            config.initializers["Event1"].switchs[0].when_rule_code
            == "(IsMajor(agemin='18') AND NOT IsEmpty(text=@Workflow.ExternalId))"
        )

    def test_literal_integer_argument_converted(self):
        config = get_config(COMPOSED)
        # '18' (chaîne) converti en int via le type déclaré INTEGER.
        seen = {}

        def probe(ctx, agemin):
            seen["agemin"] = agemin
            return True

        from urban_workflow import FunctionRegistry

        rules = FunctionRegistry("rule")
        rules.add("IsMajor", probe)
        rules.add("IsEmpty", is_empty)
        config = parse_config(COMPOSED, rules=rules)
        config.initializers["Event1"].switchs[0].when_rule(make_context(external_id="x"))
        assert seen["agemin"] == 18
        assert isinstance(seen["agemin"], int)


# ----------------------------------------------------------------------
# Golden : exemple complet du README source, repris tel quel
# ----------------------------------------------------------------------

README_PAYLOAD = """
    NAME wrk1 VERSION 2
    CONCURENCY 1
    DESCRIPTION                                 'workflow de test'
    -- you can load many configurations in the processor. the processor will evaluate what the best configuration for evaluate the workflow rules
    MATCHING (Country = 'France')

    -- define all events will interectact with the workflow
    DEFINE EVENT     Event1                     'incoming event 1';
    DEFINE EVENT     Event2                     'incoming event 2';

    --  define all rules will matchs the best swich
    DEFINE RULE      IsMajor (INTEGER agemin)   'this method 1';
    DEFINE RULE      IsEmpty (TEXT name)        'this method 2';

    --  define all actions can be triggered
    DEFINE ACTION    Cut(TEXT key)              'Remove user';

    DEFINE CONST     Name 'gael'                'ben oui c est moi';
    DEFINE CONST     agemin 18                  'min for been major';

    -- after all declarations, this line is required for initialize workflow
    INITIALIZE WORKFLOW
        ON EVENT Event1 WHEN NOT IsEmpty(name = @Event.ExternalId)
            SWITCH State1

    DEFINE STATE State1                         'state 1'
        ON ENTER STATE
            WHEN NOT IsMajor(agemin = agemin)
                EXECUTE Cut(key = @Event.ExternalId)
                     -- Cut(key = @Event.ExternalId)
                STORE   (Status = 'InProgress')
                     -- (Status = 'InProgress')

        ON EVENT Event2
            SWITCH State2

        EXPIRE AFTER 2 DAY
            SWITCH State3

    ;

    DEFINE STATE State2            'state 2'

    ;

    DEFINE STATE State3            'state 3'

    ;
"""


class TestReadmeExample:
    def get_config(self):
        from urban_workflow import FunctionRegistry

        rules = FunctionRegistry("rule")
        rules.add("IsMajor", is_major)
        rules.add("IsEmpty", lambda ctx, name: not name)
        return parse_config(README_PAYLOAD, rules=rules, filename="README")

    def test_structure(self):
        config = self.get_config()
        assert config.name == "wrk1"
        assert config.version == 2
        assert config.concurrency == 1
        assert config.filters == {"Country": "France"}
        assert len(config.states) == 3
        assert len(config.initializers) == 1
        assert len(config.declared_events) == 4

        s1 = config.states["State1"]
        assert set(s1.events) == {"Event2", constants.EXPIRED_EVENT_NAME}
        assert s1.events["Event2"].transitions[0].target_state is config.states["State2"]
        assert (
            s1.events[constants.EXPIRED_EVENT_NAME].transitions[0].target_state
            is config.states["State3"]
        )

    def test_event_path_resolves_in_extended_datas(self):
        config = self.get_config()
        cut = config.states["State1"].incoming_rules[0].actions[0]
        assert isinstance(cut.arguments["key"], ContextRef)
        assert cut.arguments["key"].path == "Event.ExternalId"

        ctx = make_context()
        ctx.event = Event(name="Event1", extended_datas={"ExternalId": "E-42"})
        assert cut.arguments["key"](ctx) == "E-42"

    def test_enter_rule_negated(self):
        config = self.get_config()
        when = config.states["State1"].incoming_rules[0].when_rule
        assert when(make_context(Age=15)) is True  # NOT IsMajor
        assert when(make_context(Age=25)) is False


# ----------------------------------------------------------------------
# Divers
# ----------------------------------------------------------------------


class TestMisc:
    def test_crc_is_set(self):
        config = get_config()
        assert config.crc != 0

    def test_filter_evaluation(self):
        config = get_config()
        assert config.evaluate_filter(
            IncomingEvent(name="Event1", extended_datas={"Country": "France"})
        )
        assert not config.evaluate_filter(
            IncomingEvent(name="Event1", extended_datas={"Country": "Germany"})
        )
        assert not config.evaluate_filter(IncomingEvent(name="Event1"))

    def test_escaped_quote_in_string(self):
        payload = """
            NAME wrk3
            DESCRIPTION 'c''est un test'
            DEFINE EVENT Event1 'l''événement' ;
        """
        config = get_config(payload)
        assert config.label == "c'est un test"
        assert config.declared_events["Event1"].label == "l'événement"

    def test_transition_labels(self):
        config = get_config()
        transition = config.states["State1"].events["Event2"].transitions[0]
        assert transition.label == "State1 -> State2"
