import contextvars
import os
import time
from collections.abc import MutableMapping
from decimal import Decimal
from typing import Any, Mapping, Optional, Union, cast

import woodchipper

LoggableValue = Optional[Union[str, int, bool, Decimal, float]]
LoggingContextType = Mapping[str, LoggableValue]


class LoggingContextVar(MutableMapping):
    _var: contextvars.ContextVar[LoggingContextType]

    def __init__(self, name):
        self._var = contextvars.ContextVar(name, default={})

    def __getitem__(self, key: str) -> str:
        return self._var.get().get(key)

    def __setitem__(self, key: str, value: LoggableValue) -> contextvars.Token:
        updated = self._var.get().copy()
        updated[key] = value
        return self._var.set(updated)

    def __eq__(self, val) -> bool:
        return val == self._var.get()

    def __delitem__(self, key: str) -> contextvars.Token:
        updated = self._var.get().copy()
        del updated[key]
        return self._var.set(updated)

    def __iter__(self):
        return self._var.get().__iter__()

    def __len__(self):
        return self._var.get().__len__()

    def __repr__(self):
        return repr(self._var.get())

    def as_dict(self):
        return self._var.get().copy()

    def update(self, d: LoggingContextType) -> contextvars.Token:
        token = None
        for key, value in d.items():
            new_token = self.__setitem__(key, value)
            if token is None:
                token = new_token
        return token

    def reset(self, token: contextvars.Token):
        self._var.reset(token)


MISSING_PREFIX = object()


class LoggingContext:
    """A context manager for logging context.

    Usage:
    ```python
    with LoggingContext(data_to_inject_to_logging_context):
        some_function()
    ```
    """

    def __init__(self, injected_context: LoggingContextType, prefix=MISSING_PREFIX):
        self.injected_context = injected_context
        self.prefix = os.getenv("WOODCHIPPER_KEY_PREFIX") if prefix is MISSING_PREFIX else prefix
        self._token = None
        self._monitors = [cls() for cls in woodchipper._monitors]
        self.start_time: Optional[float]

    def __enter__(self):
        self._token = logging_ctx.update(
            {(f"{self.prefix}.{k}" if self.prefix else k): v for k, v in self.injected_context.items()}
        )
        for monitor in self._monitors:
            monitor.setup()
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        monitored_data = {"context.time_to_run_μsec": int((time.time() - self.start_time) * 1e6)}
        for monitor in self._monitors:
            monitored_data.update(monitor.finish())
        woodchipper.get_logger(__name__).info("Exiting context.", **monitored_data)
        logging_ctx.reset(self._token)
        self._token = None
        return False


logging_ctx = LoggingContextVar("logging_ctx")


def _convert_to_loggable_value(value: Any) -> LoggableValue:
    loggable_types = {str, int, bool, Decimal, float, None}
    if type(value) in loggable_types:
        return cast(LoggableValue, value)
    else:
        try:
            return str(value)
        except Exception:
            raise ValueError(
                f"Value type (type={type(value)} is not a not a LoggableType ({str, int, bool, Decimal, float, None}) "
                f"and cannot be converted to string."
            )
