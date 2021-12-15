import json
from unittest.mock import patch

from woodchipper.processors import inject_context_processor
from woodchipper.context import LoggingContext

mock_context_items = {
    "type": "info",
    "message": "mock_message",
    "test_key_1": "test_value_1",
    "test_key_2": "test_value_2"
}

class TestInjectContextProcessor:
    def test_updates_context_with_event(self):
        event_msg = {
            "type": "debug",
            "message": "Test Event Log"
        }

        result = inject_context_processor(event_dict=event_msg)

        assert result["type"] == event_msg["type"]
        assert result["message"] == event_msg["message"]

    def test_updates_context_with_new_item(self):
        event_msg = {
            "new_key": "new_value"
        }
        result = inject_context_processor(event_dict=event_msg)

        assert result["new_key"] == event_msg["new_key"]
