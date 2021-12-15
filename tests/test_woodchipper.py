from unittest.mock import patch

from woodchipper.woodchipper import arg_logger, missing


def test_arg_logger_invokes_logging_context_with_arguments():
    @arg_logger(Foo="foo", Bar="bar", NestedObjID="key.nested_obj.id", NestValue="nest.value")
    def foo(bar, key=None, foo="hello", **kwargs):
        pass

    with patch("woodchipper.woodchipper.LoggingContext", autospec=True) as mocked:
        foo("bar value", key={"nested_obj": {"id": "some_id"}})

    assert mocked.called
    assert not mocked.call_args.kwargs
    assert mocked.call_args.args == (
        {"Bar": "bar value", "NestedObjID": "some_id", "NestValue": missing, "Foo": missing},
    )
