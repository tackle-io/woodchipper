import structlog

import woodchipper.processors
from woodchipper import BaseConfigClass

callsite_parameters = [
    structlog.processors.CallsiteParameter.FUNC_NAME,
    structlog.processors.CallsiteParameter.LINENO,
    structlog.processors.CallsiteParameter.MODULE,
]


class DevLogToStdout(BaseConfigClass):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.processors.CallsiteParameterAdder(parameters=callsite_parameters),
        woodchipper.processors.inject_context_processor,
        structlog.dev.ConsoleRenderer(),
    ]
    factory = structlog.PrintLoggerFactory()


class JSONLogToStdout(BaseConfigClass):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.processors.CallsiteParameterAdder(parameters=callsite_parameters),
        structlog.processors.format_exc_info,
        woodchipper.processors.inject_context_processor,
        structlog.processors.JSONRenderer(),
    ]
    factory = structlog.PrintLoggerFactory()
