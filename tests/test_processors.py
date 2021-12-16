import logging
from unittest.mock import patch

from woodchipper.processors import inject_context_processor

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
