import logging

import pytest

# import structlog
from structlog.testing import capture_logs

import woodchipper
from woodchipper.configs import Minimal


class TestWoodchipperLogging:
    def test_woodchipper_outputs_logs(self):
        woodchipper.configure(config=Minimal, facilities={"": "DEBUG"})
        logger = woodchipper.get_logger(__name__)

        with capture_logs() as caps_logs:
            logger.debug("Debug Log Test")
            logger.info("Info Log Test")
            logger.warning("Warning Log Test")
            logger.error("Error Log Test")
            logger.critical("Critical Log Test")
            logger.exception("Exception Log Test")

        assert caps_logs == [
            {"event": "Debug Log Test", "log_level": "debug"},
            {"event": "Info Log Test", "log_level": "info"},
            {"event": "Warning Log Test", "log_level": "warning"},
            {"event": "Error Log Test", "log_level": "error"},
            {"event": "Critical Log Test", "log_level": "critical"},
            {"exc_info": True, "event": "Exception Log Test", "log_level": "exception"},
        ]

    @pytest.mark.skip("Figure out a way to test based on what actually get handled.")
    def test_woodchipper_set_log_level(self):
        woodchipper.configure(log_level=logging.ERROR)
        logger = woodchipper.get_logger()

        with capture_logs() as caps_logs:
            logger.debug("Debug Log Test")
            logger.info("Info Log Test")
            logger.warning("Warning Log Test")
            logger.error("Error Log Test")
            logger.critical("Critical Log Test")
            logger.exception("Exception Log Test")

        assert caps_logs == [
            {"event": "Error Log Test", "log_level": "error"},
            {"event": "Critical Log Test", "log_level": "critical"},
            {"exc_info": True, "event": "Exception Log Test", "log_level": "error"},
        ]
