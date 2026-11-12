"""Tests du templating urban-json — port de la couche ``Templates/`` du source.

Triplets *template → contexte → sortie JSON attendue*, forme du template
par défaut (``TemplateModels.DefaultAction``), métadonnées qui ne
s'écrasent pas entre elles (bug §5), rappels ``$_reminder``, et scénario
DSL de bout en bout avec le ``JsltActionTranslator`` branché sur le moteur.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from test_dsl import PAYLOAD, get_config

from urban_workflow import (
    ContextRef,
    IncomingEvent,
    MemoryStorage,
    ResultActionConfig,
    RunContext,
    Workflow,
    WorkflowClock,
    WorkflowEngine,
    WorkflowFactory,
    WorkflowProcessor,
    WorkflowsConfig,
    constants,
)
from urban_workflow.outputs import default_memory_output
from urban_workflow.templating import (
    JsltActionTranslator,
    MetadataRegistry,
    TemplateRegistry,
    build_action_document,
    json_safe,
)

NOW = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)


def make_context(**incoming_extended) -> RunContext:
    factory = WorkflowFactory()
    incoming = IncomingEvent(
        name="Event1",
        external_id="ext-1",
        creation_date=NOW,
        event_date=NOW,
        integration_date=NOW,
        extended_datas=dict(incoming_extended),
    )
    workflow = factory.create_new_workflow("wrk1", 2, "ext-1", {"Country": "France"})
    ctx = factory.create_context(workflow, incoming)
    ctx.event.from_state = "State1"
    ctx.event.to_state = "State2"
    return ctx


def make_action(ctx: RunContext, **config_kwargs):
    config = ResultActionConfig(**config_kwargs)
    return config.map(ctx)


# ----------------------------------------------------------------------
# Document de contexte
# ----------------------------------------------------------------------


class TestBuildActionDocument:
    def test_document_structure(self):
        with WorkflowClock.frozen(NOW):
            ctx = make_context(Country="France", Age=25)
            action = make_action(
                ctx, name="Cut", kind=constants.PUSH_ACTION_NAME
            )
            action.arguments["key"] = "value-1"
            document = build_action_document(ctx, action)

        assert document["now"] == NOW.isoformat()

        assert document["action"]["name"] == "Cut"
        assert document["action"]["kind"] == constants.PUSH_ACTION_NAME
        assert document["action"]["arguments"] == {"key": "value-1"}
        assert document["action"]["uuid"] == str(action.uuid)

        workflow = document["workflow"]
        assert workflow["name"] == "wrk1"
        assert workflow["version"] == 2
        assert workflow["external_id"] == "ext-1"
        assert workflow["Country"] == "France"  # données étendues fusionnées

        event = document["event"]
        assert event["from_state"] == "State1"
        assert event["to_state"] == "State2"
        assert event["name"] == "Event1"
        assert event["integration_date"] == NOW.isoformat()

        incoming = document["incoming"]
        assert incoming["Age"] == 25
        assert incoming["external_id"] == "ext-1"
        assert incoming["event_date"] == NOW.isoformat()
        assert incoming["integration_date"] == NOW.isoformat()

    def test_json_safe_conversions(self):
        uuid = uuid4()
        value = {"when": NOW, "id": uuid, "nested": [{"d": NOW.date()}]}
        safe = json_safe(value)
        assert safe == {
            "when": NOW.isoformat(),
            "id": str(uuid),
            "nested": [{"d": NOW.date().isoformat()}],
        }

    def test_context_ref_argument_resolved(self):
        ctx = make_context()
        action = make_action(ctx, name="Cut")
        action.arguments["key"] = ContextRef.parse("@Workflow.ExternalId")
        document = build_action_document(ctx, action)
        assert document["action"]["arguments"] == {"key": "ext-1"}


# ----------------------------------------------------------------------
# TemplateRegistry : défaut, par action, répertoire .jslt
# ----------------------------------------------------------------------


class TestTemplateRegistry:
    def test_default_template_shape(self):
        # Même forme que TemplateModels.DefaultAction du source.
        registry = TemplateRegistry()
        with WorkflowClock.frozen(NOW):
            ctx = make_context()
            action = make_action(ctx, name="Cut", kind=constants.PUSH_ACTION_NAME)
            action.arguments["key"] = "k-1"
            body = registry.transform("Cut", build_action_document(ctx, action))

        assert body == {
            "Uuid": str(action.uuid),
            "Name": "Cut",
            "PushedAt": NOW.isoformat(),
            "Arguments": {"key": "k-1"},
            "WorkflowId": str(ctx.workflow.uuid),
            "EventId": str(ctx.event.uuid),
            "From_State": "State1",
            "To_State": "State2",
        }

    def test_action_specific_template_wins(self):
        registry = TemplateRegistry().add_template(
            "Cut", '{ "Target": $.action.arguments.key, "Who": $.workflow.external_id }'
        )
        ctx = make_context()
        action = make_action(ctx, name="Cut")
        action.arguments["key"] = "user-7"
        body = registry.transform("Cut", build_action_document(ctx, action))
        assert body == {"Target": "user-7", "Who": "ext-1"}

    def test_directory_loading_and_default(self, tmp_path):
        (tmp_path / "Cut.jslt").write_text(
            '{ "Target": $.action.arguments.key }', encoding="utf-8"
        )
        (tmp_path / "default.jslt").write_text(
            '{ "Fallback": $.action.name }', encoding="utf-8"
        )

        registry = TemplateRegistry().add_directory(tmp_path)
        assert "Cut" in registry

        ctx = make_context()
        cut = make_action(ctx, name="Cut")
        cut.arguments["key"] = "u1"
        assert registry.transform("Cut", build_action_document(ctx, cut)) == {
            "Target": "u1"
        }

        other = make_action(ctx, name="Autre")
        assert registry.transform("Autre", build_action_document(ctx, other)) == {
            "Fallback": "Autre"
        }

    def test_no_template_and_no_default_raises(self):
        registry = TemplateRegistry(default_template=None)
        with pytest.raises(LookupError, match="Inconnue"):
            registry.transform("Inconnue", {})

    def test_custom_functions(self):
        from urban_json import default_registry

        functions = default_registry.copy()
        functions.register("shout", lambda ctx, value: str(value).upper())

        registry = TemplateRegistry(functions=functions).add_template(
            "Cut", '{ "Name": shout($.action.name) }'
        )
        ctx = make_context()
        action = make_action(ctx, name="Cut")
        body = registry.transform("Cut", build_action_document(ctx, action))
        assert body == {"Name": "CUT"}


# ----------------------------------------------------------------------
# MetadataRegistry : fusion par clé (bug §5 non reproduit)
# ----------------------------------------------------------------------


class TestMetadataRegistry:
    def test_metadatas_merge_by_metadata_key(self):
        # Le source indexait par nom de template : toutes les métadonnées
        # s'écrasaient entre elles. Ici chaque clé survit.
        registry = MetadataRegistry()
        registry.add_metadata("Cut", {"canal": "sms", "priority": "high"})
        registry.add_metadata("Cut", {"ttl": "60"})
        assert registry.get("Cut") == {
            "canal": "sms",
            "priority": "high",
            "ttl": "60",
        }

    def test_same_key_is_replaced(self):
        registry = MetadataRegistry()
        registry.add_metadata("Cut", {"canal": "sms"})
        registry.add_metadata("Cut", {"canal": "mail"})
        assert registry.get("Cut") == {"canal": "mail"}

    def test_default_fallback_and_isolation(self):
        registry = MetadataRegistry(default={"canal": "bus"})
        headers = registry.get("Inconnue")
        assert headers == {"canal": "bus"}
        headers["canal"] = "mutation-locale"
        assert registry.get("Inconnue") == {"canal": "bus"}  # copie


# ----------------------------------------------------------------------
# JsltActionTranslator : MessageRaw {Header, Body} et rappels différés
# ----------------------------------------------------------------------


class TestJsltActionTranslator:
    def test_translate_produces_message_raw(self):
        metadatas = MetadataRegistry()
        metadatas.add_metadata("Cut", {"canal": "sms"})
        translator = JsltActionTranslator(metadatas=metadatas)

        with WorkflowClock.frozen(NOW):
            ctx = make_context()
            action = make_action(ctx, name="Cut", kind=constants.PUSH_ACTION_NAME)
            pushed = translator.translate(ctx, action)

        assert pushed.name == "Cut"
        assert pushed.uuid == action.uuid
        assert pushed.execute_message["Header"] == {"canal": "sms"}
        assert pushed.execute_message["Body"]["Name"] == "Cut"
        assert pushed.execute_message["Body"]["PushedAt"] == NOW.isoformat()

    def test_delayed_action_wrapped_in_reminder(self):
        metadatas = MetadataRegistry()
        metadatas.add_metadata(constants.PUSH_REMINDER, {"canal": "reminder-bus"})
        translator = JsltActionTranslator(metadatas=metadatas)

        with WorkflowClock.frozen(NOW):
            ctx = make_context()
            action = make_action(
                ctx, name="Cut", kind=constants.PUSH_ACTION_NAME, delay=120
            )
            pushed = translator.translate(ctx, action)

        message = pushed.execute_message
        assert message["Header"] == {"canal": "reminder-bus"}
        body = message["Body"]
        assert body["Name"] == constants.PUSH_REMINDER
        assert body["Delay"] == 120
        assert body["Uuid"] == str(action.uuid)
        # Le corps réel de l'action est encapsulé sous Message.
        assert body["Message"]["Name"] == "Cut"
        assert body["Message"]["Arguments"] == {}


# ----------------------------------------------------------------------
# Bout en bout : moteur + DSL + templates JSLT
# ----------------------------------------------------------------------


class TestEndToEnd:
    def make_engine(self, translator: JsltActionTranslator):
        storage = MemoryStorage()
        configs = WorkflowsConfig().add_document(get_config(PAYLOAD))
        processor = WorkflowProcessor(
            configs, WorkflowFactory(), translator=translator
        )
        processor.load_existing_workflows_by_external_id = lambda key: storage.get_by(
            Workflow, key, "external_id"
        )
        processor.output_actions = default_memory_output(storage)
        return WorkflowEngine(processor), storage

    def test_dsl_scenario_with_jslt_templates(self):
        templates = TemplateRegistry().add_template(
            "Cut",
            '{ "Order": "cut", "Key": $.action.arguments.key,'
            ' "Country": $.incoming.Country }',
        )
        engine, storage = self.make_engine(JsltActionTranslator(templates))

        external_id = str(uuid4())
        engine.evaluate_event(
            {
                "Name": "Event1",
                "Uuid": str(uuid4()),
                "ExternalId": external_id,
                "Country": "France",
                "Age": 25,
            }
        )

        workflow = storage.get_all(Workflow)[0]
        assert workflow.current_state == "State1"

        pushed = {action.name: action for action in workflow.last_event.actions}
        # Cut : template dédié, argument @Workflow.ExternalId résolu.
        cut_body = pushed["Cut"].execute_message["Body"]
        assert cut_body == {
            "Order": "cut",
            "Key": external_id,
            "Country": "France",
        }
        # Rappel d'expiration : enveloppe $_reminder + corps au template défaut.
        reminder_body = pushed[constants.EXPIRED_EVENT_NAME].execute_message["Body"]
        assert reminder_body["Name"] == constants.PUSH_REMINDER
        assert reminder_body["Delay"] == 2 * 24 * 60
        assert reminder_body["Message"]["Name"] == constants.EXPIRED_EVENT_NAME
        assert reminder_body["Message"]["WorkflowId"] == str(workflow.uuid)
