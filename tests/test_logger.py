import contextlib
import io
import json
import os
from unittest.mock import patch

import woodchipper
import woodchipper.configs


def test_bind_log_prefix():
    with patch.dict(os.environ, dict(WOODCHIPPER_KEY_PREFIX="footest")):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            woodchipper.configure(config=woodchipper.configs.Minimal, facilities={"": "INFO"})
            logger = woodchipper.get_logger(__name__)
            logger.info("Message one.", a=1)
            logger_with_ctx = logger.bind(**{"b": 2, "customprefix.bar": "baz"})
            logger_with_ctx.info("Message two.", a=1)
        messages = [json.loads(message) for message in buf.getvalue().strip().split("\n")]
        assert messages[0]["event"] == "Message one."
        assert messages[0]["level"] == "info"
        assert messages[0]["footest.a"] == 1
        assert messages[1]["footest.b"] == 2
        assert messages[1]["customprefix.bar"] == "baz"
        assert messages[1]["footest.a"] == 1
