import logging
from unittest.mock import patch

import pytest
import structlog

from woodchipper.processors import (
    inject_context_processor,
    _match_name_to_closest_facility,
    minimum_log_level_processor,
)

mock_context_items = {
    "type": "info",
    "message": "mock_message",
    "test_key_1": "test_value_1",
    "test_key_2": "test_value_2",
}


class TestInjectContextProcessor:
    @patch("woodchipper.context.logging_ctx.as_dict", return_value=mock_context_items)
    def test_updates_context_with_event(self, context_items):
        event_msg = {"type": "debug", "message": "Test Event Log"}

        result = inject_context_processor(logging.getLogger(), "info", event_dict=event_msg)

        assert result["type"] == event_msg["type"]
        assert result["message"] == event_msg["message"]
        assert result["test_key_1"] == mock_context_items["test_key_1"]
        assert result["test_key_2"] == mock_context_items["test_key_2"]

    @patch("woodchipper.context.logging_ctx.as_dict", return_value=mock_context_items)
    def test_updates_context_with_new_item(self, context_items):
        event_msg = {"new_key": "new_value"}
        result = inject_context_processor(logging.getLogger(), "info", event_dict=event_msg)

        assert result["new_key"] == event_msg["new_key"]
        assert result["test_key_1"] == mock_context_items["test_key_1"]


@pytest.mark.parametrize(
    argnames=["candidate_to_facility_mapping", "full_path", "facility_level_pair"],
    argvalues=[
        ({"foo": "foo_level", "bar": "bar_level"}, "foo", ("foo", "foo_level")),
        ({"foo": "foo_level", "foo.bar": "foo.bar_level"}, "foo", ("foo", "foo_level")),
        ({"foo": "foo_level", "foo.bar": "foo.bar_level"}, "foo.bar", ("foo.bar", "foo.bar_level")),
        ({"foo": "foo_level", "foo.baz": "foo.baz_level"}, "foo.bar.quux", ("foo", "foo_level")),
        ({"foo": "foo_level"}, "baz", None),
        ({}, "baz", None),
        ({"": "emtpy_string_entry"}, "foo", ("", "emtpy_string_entry")),
        ({"": "emtpy_string_entry", "foo": "foo_value"}, "bar", ("", "emtpy_string_entry")),
        ({"foo.bar": "foo.bar_level", "foo.barz": "foo.barz_level"}, "foo.bar", ("foo.bar", "foo.bar_level")),
    ],
)
def test_match_name_to_closest_facility(candidate_to_facility_mapping, full_path, facility_level_pair):
    assert _match_name_to_closest_facility(full_path, candidate_to_facility_mapping) == facility_level_pair


class TestMinimumLogLevelProcessor__root_info_and_named_info:
    """Test when root level (empty string) is INFO and named is INFO"""

    @pytest.fixture(scope="class")
    def facilities(self):
        return {"": "INFO", "test.bar": "INFO"}

    @pytest.fixture(scope="class", autouse=True)
    def get_facilities_stub(self, facilities):
        with patch("woodchipper.processors.get_facilities", autospec=True) as stub:
            stub.return_value = facilities
            yield

    @pytest.fixture(scope="class")
    def named_logger(self):
        return logging.getLogger("test.bar.foo")

    @pytest.fixture(scope="class")
    def unnamed_logger(self):
        return logging.getLogger("unknown_logger")

    def test_named_logger_below_facility_config(self, named_logger):
        with pytest.raises(structlog.DropEvent):
            minimum_log_level_processor(named_logger, "debug", {})

    def test_named_logger_at_facility_config(self, named_logger):
        # Would raise if rejected
        assert minimum_log_level_processor(named_logger, "info", {}) == {}

    def test_named_logger_above_facility_config(self, named_logger):
        # Would raise if rejected
        assert minimum_log_level_processor(named_logger, "error", {}) == {}

    def test_unnamed_logger_below_facility_config(self, unnamed_logger):
        with pytest.raises(structlog.DropEvent):
            minimum_log_level_processor(unnamed_logger, "debug", {})

    def test_unnamed_logger_at_facility_config(self, unnamed_logger):
        # Would raise if rejected
        assert minimum_log_level_processor(unnamed_logger, "info", {}) == {}

    def test_unnamed_logger_above_facility_config(self, unnamed_logger):
        # Would raise if rejected
        assert minimum_log_level_processor(unnamed_logger, "error", {}) == {}
