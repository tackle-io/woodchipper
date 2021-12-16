import logging
import woodchipper

from structlog.testing import capture_logs, CapturingLoggerFactory

class TestWoodchipperLogging:
    def test_woodchipper_outputs_logs(self):
        cf = CapturingLoggerFactory()
        woodchipper.configure(
            log_level=logging.DEBUG,
            factory=cf
        )
        logger = woodchipper.get_logger()

        with capture_logs() as caps_logs:
            logger.debug("Debug Log Test")
            logger.info("Info Log Test")
            logger.warning("Warning Log Test")
            logger.error("Error Log Test")
            logger.critical("Critical Log Test")
            logger.exception("Exception Log Test")

        assert caps_logs == [
            {'event': 'Debug Log Test', 'log_level': 'debug'},
            {'event': 'Info Log Test', 'log_level': 'info'},
            {'event': 'Warning Log Test', 'log_level': 'warning'},
            {'event': 'Error Log Test', 'log_level': 'error'},
            {'event': 'Critical Log Test', 'log_level': 'critical'},
            {'exc_info': True, 'event': 'Exception Log Test', 'log_level': 'error'}
        ]
