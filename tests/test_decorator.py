from types import SimpleNamespace
from unittest.mock import patch

import pytest

from woodchipper.decorator import arg_logger, missing, pluck_value


def test_arg_logger_invokes_logging_context_with_arguments():
    @arg_logger(Foo="foo", Bar="bar", NestedObjID="key.nested_obj.id", NestValue="nest.value")
    def foo(bar, key=None, foo="hello", **kwargs):
        pass

    with patch("woodchipper.decorator.LoggingContext", autospec=True) as mocked:
        foo("bar value", key={"nested_obj": {"id": "some_id"}})

    assert mocked.called
    assert not mocked.call_args.kwargs
    assert mocked.call_args.args == (
        {"Bar": "bar value", "NestedObjID": "some_id", "NestValue": missing, "Foo": missing},
    )


@pytest.mark.parametrize(
    argnames=[
        "obj",
        "path_name",
        "delimiter",
        "return_value",
    ],
    argvalues=[
        ({"foo": "bar"}, "foo", ".", "bar"),
        ({"foo": {"baz": "quux"}}, "foo", ".", {"baz": "quux"}),
        ({"foo": {"baz": {"quux": 42}}}, "foo.baz.quux", ".", 42),
        ({"foo": "nope"}, "baz", ".", missing),
        ({"foo": {"baz": {"nope": 42}}}, "foo.baz.quux", ".", missing),
        ({"foo": SimpleNamespace(foo=42)}, "foo.foo", ".", 42),
        ({"foo": SimpleNamespace(foo={"baz": "bar"})}, "foo.foo.baz", ".", "bar"),
        ({"foo": SimpleNamespace(foo={"baz": "bar"})}, "foo.quux.baz", ".", missing),
        ({"bar": SimpleNamespace()}, "foo", ".", missing),
        ({"foo": SimpleNamespace(foo={"b.a.z": "bar"})}, "foo#foo#b.a.z", "#", "bar"),
        ({"f.o.o": SimpleNamespace(foo={"baz": "bar"})}, "f.o.o#foo#baz", "#", "bar"),
        ({"bar": SimpleNamespace()}, "bar", "#", SimpleNamespace()),
    ],
)
def test_pluck_value(obj, path_name, delimiter, return_value):
    assert pluck_value(obj, path_name, delimiter=delimiter) == return_value
