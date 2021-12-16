from typing import Callable, Dict, List, Set, Type

import structlog

from woodchipper.monitors import BaseMonitor

_monitors: Set[Type[BaseMonitor]] = set()
_facilities: Dict[str, str] = {}


class BaseConfigClass:
    processors: List[Callable]
    factory: Callable


def configure(config: BaseConfigClass, facilities: Dict[str, str], monitors: List[Type[BaseMonitor]]) -> None:
    _monitors.update(set(monitors))
    _facilities.update(facilities)
    structlog.configure(
        processors=config.processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def reset():
    structlog.reset_defaults()


def get_monitors():
    return list(_monitors)


def get_facilities():
    return _facilities


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
