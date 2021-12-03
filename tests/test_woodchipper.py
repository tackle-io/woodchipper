import logging

import pytest

from tests.utilities import InspectableLoggerAdapter
from woodchipper import _CapturedLoggerAdapter, arg_logger


def test_captured_logger_adapter():
    class SimpleLoggerAdapterInterface:
        def __init__(self, extra):
            self.extra = extra

    logger = SimpleLoggerAdapterInterface({"before_context": {"nested": "value"}})

    assert logger.extra == {"before_context": {"nested": "value"}}

    with _CapturedLoggerAdapter(logger, {"additional": "info"}):
        assert logger.extra == {"before_context": {"nested": "value"}, "additional": "info"}

    assert logger.extra == {"before_context": {"nested": "value"}}


def test_arg_logger_happy_path():
    logger = InspectableLoggerAdapter(logging.getLogger(), {"before function": "begins"})

    @arg_logger(logger, Foo="foo", bar="Bar", key="Key_Name", NestValue="nest.value")
    def foo(bar, key=None, foo="hello", **kwargs):
        logger.info("Logged message from within foo")

    logger.info("Logged before foo is executed")
    foo("bar value", key="key value")
    logger.info("Logged after foo is executed")

    breakpoint()
