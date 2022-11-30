import importlib
import logging
import os

import structlog

try:
    from structlog_sentry import SentryJsonProcessor
except ImportError:
    # structlog_sentry is an optional dependency
    # if not installed, make a no-op processor
    class SentryJsonProcessor:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, logger, name, event_dict):
            return event_dict


import woodchipper.logger
import woodchipper.processors
from woodchipper import BaseConfigClass

callsite_parameters = [
    structlog.processors.CallsiteParameter.FUNC_NAME,
    structlog.processors.CallsiteParameter.LINENO,
    structlog.processors.CallsiteParameter.MODULE,
]


# Users can override color style
if os.getenv("WOODCHIPPER_COLOR_STYLE") is not None:
    _style_mod_name, _style_var_name = os.environ["WOODCHIPPER_COLOR_STYLE"].rsplit(".", 1)
    _style_mod = importlib.import_module(_style_mod_name)
    _style_dict = getattr(_style_mod, _style_var_name)
else:
    _style_dict = None


class Minimal(BaseConfigClass):
    """
    Really used for unit tests. That's it.
    """

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = woodchipper.logger.BoundLogger
    renderer = structlog.processors.JSONRenderer()


class DevLogToStdout(BaseConfigClass):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.processors.CallsiteParameterAdder(
            parameters=callsite_parameters, additional_ignores=["woodchipper"]
        ),
        woodchipper.processors.inject_context_processor,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = woodchipper.logger.BoundLogger
    renderer = structlog.dev.ConsoleRenderer(
        colors=not os.getenv("WOODCHIPPER_DISABLE_COLORS"), level_styles=_style_dict
    )


class JSONLogToStdout(BaseConfigClass):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        woodchipper.processors.GitVersionProcessor(),
        woodchipper.processors.DatadogTraceProcessor(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.processors.CallsiteParameterAdder(
            parameters=callsite_parameters, additional_ignores=["woodchipper"]
        ),
        SentryJsonProcessor(level=logging.ERROR, as_extra=True, active=not os.getenv("WOODCHIPPER_DISABLE_SENTRY")),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        woodchipper.processors.inject_context_processor,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = woodchipper.logger.BoundLogger
    renderer = structlog.processors.JSONRenderer()
