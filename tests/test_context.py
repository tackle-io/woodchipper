from woodchipper.context import LoggingContextVar


def test_logging_context_var():
    var = LoggingContextVar("var")

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
