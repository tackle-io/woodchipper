import contextvars
from collections.abc import MutableMapping
from decimal import Decimal
from typing import Mapping, Optional, Union

LoggableValue = Optional[Union[str, int, bool, Decimal, float]]
LoggingContext = Mapping[str, LoggableValue]


class LoggingContextVar(MutableMapping):
    _var: contextvars.ContextVar[LoggingContext]

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
        return self._var.get()

    def update(self, d: LoggingContext) -> contextvars.Token:
        token = None
        for key, value in d.items():
            new_token = self.__setitem__(key, value)
            if token is None:
                token = new_token
        return token

    def reset(self, token: contextvars.Token):
        self._var.reset(token)


logging_ctx = LoggingContextVar("logging_ctx")
