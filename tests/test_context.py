from unittest.mock import patch

from woodchipper import context


def test_logging_context_var():
    var = context.LoggingContextVar("var")

    # We start off empty
    assert var == {}

    # Setting an item returns a token and sets the item
    tkn = var.__setitem__("a", 1)
    assert tkn
    assert var == dict(a=1)

    # That token can be used to reset
    var.reset(tkn)
    assert var == {}

    # Update should return a token and perform the dict update
    tkn1 = var.update(dict(a=1, b=2))
    assert var == dict(a=1, b=2)
    tkn2 = var.update(dict(a=3, c=4))
    assert var == dict(a=3, b=2, c=4)
    # Single key access should work without side-effect
    assert var["a"] == 3

    # The tokens can be used to reset back to each prior stage
    var.reset(tkn2)
    assert var == dict(a=1, b=2)
    var.reset(tkn1)
    assert var == {}


def test_logging_context_prefix():
    assert context.logging_ctx.as_dict() == {}
    ctx_obj = context.LoggingContext("test-name", a=1, _prefix="test")
    with ctx_obj:
        assert context.logging_ctx.as_dict() == {"test.a": 1}

    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="env"):
        with context.LoggingContext(a=1):
            assert context.logging_ctx.as_dict() == {"env.a": 1}

    with context.LoggingContext(a=1, _prefix=None):
        assert context.logging_ctx.as_dict() == {"a": 1}


def test_logging_context_log_level():
    assert context.logging_ctx.as_dict() == {}
    ctx_obj = context.LoggingContext("test-name", a=1, _prefix="test")
    with ctx_obj:
        assert context.logging_ctx.as_dict() == {"test.a": 1}

    with patch.dict("woodchipper.context.os.environ", WOODCHIPPER_KEY_PREFIX="env"):
        with context.LoggingContext(a=1):
            assert context.logging_ctx.as_dict() == {"env.a": 1}

    with context.LoggingContext(a=1, _prefix=None):
        assert context.logging_ctx.as_dict() == {"a": 1}


def test_logging_context_name():
    ctx_obj = context.LoggingContext("test-name", a=1, _prefix="test")
    with ctx_obj:
        assert ctx_obj.name == "test-name"
    assert ctx_obj.name == "test-name"

    ctx_obj = context.LoggingContext(a=1, _prefix="test")
    with ctx_obj:
        assert ctx_obj.name == "test_context:test_logging_context_name"
    assert ctx_obj.name == "test_context:test_logging_context_name"

    ctx_obj = context.LoggingContext("test-name", a="x", _prefix="test")

    @ctx_obj
    def f(x):
        assert ctx_obj.name == "test-name"

    f(1)
    assert ctx_obj.name == "test-name"

    ctx_obj = context.LoggingContext(a="x", _prefix="test")

    @ctx_obj
    def f(x):
        assert ctx_obj.name == "test_context:f"

    f(1)
    assert ctx_obj.name == "test_context:f"
