import inspect
import logging
from copy import deepcopy
from functools import wraps
from typing import Tuple, Union, NamedTuple, Dict, Mapping


class _Missing:
    def __repr__(self):
        return "<missing>"


missing = _Missing()


def _split_head_node(str_path: str, delimiter=".") -> Tuple[str, str]:
    head, *tail = str_path.split(delimiter)
    return head, delimiter.join(tail)


def _get_key_or_attr(obj, name: str, missing=missing):
    try:
        return getattr(obj, name)
    except AttributeError:
        pass
    try:
        return obj[name]
    except (TypeError, KeyError):
        pass

    return missing


def _pluck_value(obj, str_path: str, delimiter=".") -> Union[str, _Missing]:
    if not str_path:
        return obj
    else:
        head, *remaining = _split_head_node(str_path, delimiter)
        value = _get_key_or_attr(obj, head)
        if value is missing:
            return missing
        else:
            return _pluck_value(value, delimiter.join(remaining), delimiter)


class ParamSearchConfig(NamedTuple):
    dig_path: str
    logger_name: str
    diggable: bool


def _build_path_head_to_param_config_map(kwargs: Mapping, *, delimiter: str = '.') -> Mapping[str, ParamSearchConfig]:
    return_mapping = {}
    for logger_name, dig_path in kwargs.items():
        if dig_path == '':
            raise ValueError("Dig path cannot be an empty string")
        dig_head, *remaining_dig_parts = dig_path.split(delimiter)
        return_mapping[dig_head] = ParamSearchConfig(
            dig_path=delimiter.join(remaining_dig_parts),
            logger_name=logger_name,
            diggable=True if remaining_dig_parts else False
        )

    return return_mapping


class _CapturedLogger:
    def __init__(self, logger, addl_extra: Mapping):
        self.logger = logger
        self.addl_extra = addl_extra
        self._logger_start_state = deepcopy(logger)

    def __enter__(self):
        if not hasattr(self.logger, 'extra'):
            self.logger = logging.LoggerAdapter(self.logger, self.addl_extra)
        else:
            self.logger.extra = {**self.logger.extra, **self.addl_extra}

    def __exit__(self, exc_type, exc_val, exc_tb):
        # reset the logger and return False so that exceptions aren't trapped
        self.logger = self._logger_start_state
        return False


class arg_logger:
    def __init__(self, logger, /, missing_default=missing, path_delimiter='.', **decorator_kwargs):
        self.old_logger = logger
        self.decorator_kwargs = decorator_kwargs
        self.missing_default = missing_default
        self.working_extra = dict
        self.path_delimiter = path_delimiter

        self.decorator_mapping = _build_path_head_to_param_config_map(decorator_kwargs, delimiter=path_delimiter)

    def __call__(self, f):
        @wraps(f)
        def wrapper(*func_args, **func_kwargs):
            extra = self.working_extra()
            print("args", func_args)
            print("kwargs", func_kwargs)
            print("decorator mapping", self.decorator_mapping)

            # This will pair up the function signature parameters with the arguments that were passed. It's ...amazing.
            # If we wanted to apply defaults as well (that weren't passed but were defined as defaults in the
            # signature, there's a fairly easy process for that too through this api as well.

            # Note: We not will dig into the *args or **kwargs of the function, if the function definition used
            # *args or **kwargs. It's more difficult for **kwargs and not possible with *args.
            mapped_args = inspect.signature(f).bind(*func_args, **func_kwargs).arguments

            for dec_param_name, param_config_entry in self.decorator_mapping.items():
                if dec_param_name not in mapped_args:
                    extra[param_config_entry.logger_name] = missing
                else:
                    value_candidate = mapped_args[dec_param_name] # if not diggable, this will be the actual value
                    if param_config_entry.diggable:
                        extra[param_config_entry.logger_name] = _pluck_value(value_candidate, param_config_entry.dig_path,
                                                                 delimiter=self.path_delimiter)
                    else:
                        extra[param_config_entry.logger_name] = value_candidate

            print("created logger dict", extra)

            with _CapturedLogger(self.old_logger, extra):
                return f(*func_args, **func_kwargs)

        return wrapper
