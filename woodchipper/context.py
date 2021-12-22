import contextvars
import inspect
import os
import time
from collections.abc import MutableMapping
from decimal import Decimal
from functools import wraps
from typing import Any, Mapping, NamedTuple, Optional, Tuple, Union, cast

import woodchipper

LoggableValue = Optional[Union[str, int, bool, Decimal, float]]
LoggingContextType = Mapping[str, LoggableValue]


class Missing:
    """A sentinel value to be raised if something is missing."""

    def __repr__(self):
        return "<missing>"


# Poor mans singleton
missing = Missing()


def _split_head_node(str_path: str, delimiter=".") -> Tuple[str, str]:
    head, tail = str_path.split(delimiter, maxsplit=1) if delimiter in str_path else (str_path, "")
    return head, tail


def _get_key_or_attr(obj, name: str, missing=missing):
    try:
        return getattr(obj, name)
    except AttributeError:
        try:
            return obj[name]
        except (TypeError, KeyError):
            return missing


def pluck_value(obj, str_path: str, delimiter=".") -> Union[Any, Missing]:
    """Dig into an object or dict Using a JMSE-like path syntax. Return Missing if value cannot be found. Only
    supports mapping-like behavior so cannot search sequences."""
    if not str_path:
        return obj
    else:
        head, remaining = _split_head_node(str_path, delimiter)
        value = _get_key_or_attr(obj, head)
        if value is missing:
            return missing
        else:
            return pluck_value(value, remaining, delimiter)


class ParamSearchConfig(NamedTuple):
    dig_path: str
    logvar_name: str
    diggable: bool


def _build_path_head_to_param_config_map(kwargs: Mapping, *, delimiter: str = ".") -> Mapping[str, ParamSearchConfig]:
    return_mapping = {}
    for logvar_name, dig_path in kwargs.items():
        if dig_path == "":
            raise ValueError("Dig path cannot be an empty string")

        dig_path_head, dig_path_tail = _split_head_node(dig_path, delimiter)

        return_mapping[dig_path_head] = ParamSearchConfig(
            dig_path=dig_path_tail,
            logvar_name=logvar_name,
            diggable=True if dig_path_tail else False,
        )

    return return_mapping


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


class LoggingContext:
    """A context manager for logging context. Can also be used as a decorator.

    Usage:
    ```python
    with LoggingContext(data_to_inject_to_logging_context):
        some_function()
    ```
    """

    def __init__(self, *, prefix=missing, missing_default=missing, path_delimiter=".", **kwargs: LoggingContextType):
        # If
        self.injected_context = kwargs
        self.prefix = os.getenv("WOODCHIPPER_KEY_PREFIX") if prefix is missing else prefix
        self._token = None
        self._monitors = [cls() for cls in woodchipper._monitors]
        self.missing_default = missing_default
        self.path_delimiter = path_delimiter
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

    def __call__(self, f):
        self.decorator_mapping = _build_path_head_to_param_config_map(
            self.injected_context, delimiter=self.path_delimiter
        )

        @wraps(f)
        def wrapper(*func_args, **func_kwargs):

            # This will pair up the function signature parameters with the arguments that were passed. It's ...amazing.
            # If we wanted to apply defaults as well (that weren't passed but were defined as defaults in the
            # signature, there's a fairly easy process for that too through this api as well).

            # Note: We not will dig into the *args or **kwargs of the function, if the function definition used
            # *args or **kwargs. It's more difficult for **kwargs and not possible with *args.
            # TODO: attempt digging into function **kwargs as well?
            # TODO: consider a configurable 'log_defaults' decorator parameter that will allow the logging of
            #  function definition defaults when those arguments aren't passed to the function
            mapped_args = inspect.signature(f).bind(*func_args, **func_kwargs).arguments

            self.injected_context = {}

            # TODO: extract this functionality so that it's unit testable
            for dec_param_name, param_config_entry in self.decorator_mapping.items():
                if dec_param_name not in mapped_args:
                    raw_value = self.missing_default
                else:
                    if param_config_entry.diggable:
                        raw_value = pluck_value(
                            mapped_args[dec_param_name],
                            param_config_entry.dig_path,
                            delimiter=self.path_delimiter,
                        )
                    else:
                        raw_value = mapped_args[dec_param_name]

                self.injected_context[param_config_entry.logvar_name] = _convert_to_loggable_value(raw_value)

            with self:
                return f(*func_args, **func_kwargs)

        return wrapper


logging_ctx = LoggingContextVar("logging_ctx")
