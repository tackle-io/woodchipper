import importlib
import os
from unittest.mock import patch

import woodchipper
import woodchipper.configs


def test_log_errors_to_sentry():
    woodchipper.configure(config=woodchipper.configs.JSONLogToStdout, facilities={"": "INFO"})
    logger = woodchipper.get_logger(__name__)

    with patch("structlog_sentry.capture_event") as mock_capture_event:
        try:
            raise ValueError("Uh-oh spaghetti-o's")
        except ValueError:
            logger.exception("Bad news, friend.")
        assert mock_capture_event.called
        events, hint = mock_capture_event.call_args
        event = events[0]
        assert event["message"] == "Bad news, friend."
        assert event["extra"]["event"] == "Bad news, friend."
        assert "exception" in event

    with patch("structlog_sentry.capture_event") as mock_capture_event:
        logger.info("No issue here.")
        assert not mock_capture_event.called


def test_sentry_can_be_disabled():
    try:
        with patch.dict(os.environ, {"WOODCHIPPER_DISABLE_SENTRY": "1"}):
            # With the patched environment variable getter, we have to reload configs for it to take effect
            importlib.reload(woodchipper.configs)
            woodchipper.configure(config=woodchipper.configs.JSONLogToStdout, facilities={"": "INFO"})
            logger = woodchipper.get_logger(__name__)
            with patch("structlog_sentry.capture_event") as mock_capture_event:
                logger.error("Panic. Everybody panic.")
                assert not mock_capture_event.called
    finally:
        # Restore the configs to factory defaults
        importlib.reload(woodchipper.configs)
