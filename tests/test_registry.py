"""Tests du registre de règles/actions et de la validation des signatures."""

import pytest

from urban_workflow import (
    DuplicatedArgumentNameError,
    FunctionRegistry,
    InvalidArgumentNameError,
    InvalidMethodReferenceError,
    MissingArgumentNameError,
)


@pytest.fixture
def rules() -> FunctionRegistry:
    registry = FunctionRegistry("rule")

    @registry.register("IsMajor")
    def is_major(ctx, agemin):
        return ctx.incoming_event.extended_datas["age"] >= agemin

    @registry.register()
    def IsEmpty(ctx, name=""):
        return not name

    return registry


def test_register_and_get(rules):
    assert "IsMajor" in rules
    assert "IsEmpty" in rules  # nom par défaut = nom de la fonction
    assert callable(rules.get("IsMajor"))


def test_get_unknown_raises(rules):
    with pytest.raises(InvalidMethodReferenceError):
        rules.get("Unknown")


def test_duplicate_registration_raises(rules):
    with pytest.raises(DuplicatedArgumentNameError):
        rules.add("IsMajor", lambda ctx: True)


def test_validate_call_ok(rules):
    rules.validate_call("IsMajor", ["agemin"])
    rules.validate_call("IsEmpty", [])  # argument avec défaut : optionnel


def test_validate_call_unknown_function(rules):
    with pytest.raises(InvalidMethodReferenceError):
        rules.validate_call("Unknown", [])


def test_validate_call_unknown_argument(rules):
    with pytest.raises(InvalidArgumentNameError) as exc:
        rules.validate_call("IsMajor", ["agemax"])
    assert "agemax" in str(exc.value)


def test_validate_call_missing_argument(rules):
    with pytest.raises(MissingArgumentNameError) as exc:
        rules.validate_call("IsMajor", [])
    assert "agemin" in str(exc.value)


def test_validate_call_duplicated_argument(rules):
    with pytest.raises(DuplicatedArgumentNameError):
        rules.validate_call("IsMajor", ["agemin", "agemin"])


def test_validate_call_var_kwargs_accepts_anything():
    registry = FunctionRegistry("action")
    registry.add("Push", lambda ctx, **kwargs: kwargs)
    registry.validate_call("Push", ["anything", "goes"])
