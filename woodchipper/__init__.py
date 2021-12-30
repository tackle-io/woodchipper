import importlib
import logging.config
from typing import Callable, Dict, List, Set, Type, Union

import structlog

from woodchipper.monitors import BaseMonitor

_monitors: Set[Type[BaseMonitor]] = set()
_facilities: Dict[str, str] = {}


class BaseConfigClass:
    processors: List[Callable]
    factory: Callable
    wrapper_class: Type
    renderer: Callable


def configure(
    *,
    config: Union[str, Type[BaseConfigClass]] = "woodchipper.configs.DevLogToStdout",
    facilities: Dict[str, str] = {"": "INFO"},
    override_existing: bool = True,
    monitors: List[Type[BaseMonitor]] = [],
) -> None:
    _monitors.update(set(monitors))
    _facilities.update(facilities)
    if isinstance(config, str):
        module_name, cls_name = config.rsplit(".", 1)
        module_obj = importlib.import_module(module_name)
        config = getattr(module_obj, cls_name)
        assert isinstance(config, type)
    dict_config = {
        "version": 1,
        "disable_existing_loggers": override_existing,
        "formatters": {
            "structlog": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": config.processors,
                "processors": [structlog.stdlib.ProcessorFormatter.remove_processors_meta, config.renderer],
            }
        },
        "handlers": {
            "woodchipper": {
                "level": "DEBUG",
                "formatter": "structlog",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            facility: {"handlers": ["woodchipper"], "level": level, "propagate": False}
            for facility, level in facilities.items()
        },
    }
    logging.config.dictConfig(dict_config)

    structlog.configure(
        processors=config.processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=config.wrapper_class,
        context_class=dict,
        logger_factory=config.factory,
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
