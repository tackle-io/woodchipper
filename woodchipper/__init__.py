import logging
import structlog

from structlog import get_logger as get_logger
from typing import Any, List


DEFAULT_DEV_PROCESSORS = [
    structlog.stdlib.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
    structlog.dev.ConsoleRenderer()
]

DEPLOYMENT_PROCESSORS = [
    structlog.stdlib.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
    structlog.processors.JSONRenderer()
]

def configure(
    environment: str = None,
    log_level: int = logging.INFO,
    processors: List = None,
    factory: Any = structlog.stdlib.LoggerFactory()
) -> None:

    if not processors:
        processors = DEPLOYMENT_PROCESSORS

        if environment == 'development':
            processors = DEFAULT_DEV_PROCESSORS

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=factory,
        cache_logger_on_first_use=False
    )
