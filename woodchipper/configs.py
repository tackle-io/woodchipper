import structlog

import woodchipper.processors
from woodchipper import BaseConfigClass

callsite_parameters = [
    structlog.processors.CallsiteParameter.FUNC_NAME,
    structlog.processors.CallsiteParameter.LINENO,
    structlog.processors.CallsiteParameter.MODULE,
]


class Minimal(BaseConfigClass):
    """
    Really used for unit tests. That's it.
    """

    processors = [
        structlog.stdlib.add_log_level,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = structlog.stdlib.BoundLogger
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
        structlog.processors.CallsiteParameterAdder(parameters=callsite_parameters),
        woodchipper.processors.inject_context_processor,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = structlog.stdlib.BoundLogger
    renderer = structlog.dev.ConsoleRenderer()


class JSONLogToStdout(BaseConfigClass):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        woodchipper.processors.GitVersionProcessor(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.processors.CallsiteParameterAdder(parameters=callsite_parameters),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        woodchipper.processors.inject_context_processor,
    ]
    factory = structlog.stdlib.LoggerFactory()
    wrapper_class = structlog.stdlib.BoundLogger
    renderer = structlog.processors.JSONRenderer()
