import inspect
from copy import deepcopy
from functools import wraps
from typing import Mapping, NamedTuple, Tuple, Union


class _Missing:
    def __repr__(self):
        return "<missing>"


missing = _Missing()


def _split_head_node(str_path: str, delimiter=".") -> Tuple[str, str]:
    head, tail = str_path.split(delimiter, 1) if delimiter in str_path else str_path, ""
    return head, tail


def _get_key_or_attr(obj, name: str, missing=missing):
    try:
        return getattr(obj, name)
    except AttributeError:
        try:
            return obj[name]
        except (TypeError, KeyError):
            return missing


def _pluck_value(obj, str_path: str, delimiter=".") -> Union[str, _Missing]:
    if not str_path:
        return str(obj)
    else:
        head, remaining = _split_head_node(str_path, delimiter)
        value = _get_key_or_attr(obj, head)
        if value is missing:
            return missing
        else:
            return _pluck_value(value, remaining, delimiter)


class ParamSearchConfig(NamedTuple):
    dig_path: str
    logger_name: str
    diggable: bool


def _build_path_head_to_param_config_map(
    kwargs: Mapping[str, str], *, delimiter: str = "."
) -> Mapping[str, ParamSearchConfig]:
    return_mapping = {}
    for logger_name, dig_path in kwargs.items():
        if dig_path == "":
            raise ValueError("Dig path cannot be an empty string")
        dig_head, remaining_dig_parts = dig_path.split(delimiter, 1) if delimiter in dig_path else (dig_path, "")
        return_mapping[dig_head] = ParamSearchConfig(
            dig_path=remaining_dig_parts,
            logger_name=logger_name,
            diggable=True if remaining_dig_parts else False,
        )

    return return_mapping


class _CapturedLoggerAdapter:
    def __init__(self, logger, addl_extra: Mapping):
        self.logger = logger
        self.addl_extra = addl_extra
        self._old_extra = deepcopy(logger.extra)

    def __enter__(self):
        self.logger.extra = {**self.logger.extra, **self.addl_extra}

    def __exit__(self, exc_type, exc_val, exc_tb):
        # reset the logger and return False so that exceptions aren't trapped
        self.logger.extra = self.logger.extra = self._old_extra
        return False


class arg_logger:
    def __init__(self, logger, /, missing_default=missing, path_delimiter=".", **decorator_kwargs):
        if not hasattr(logger, "extra"):
            raise ValueError(
                f"The first argument to arg_logger must be an object with a mutable 'extra' attribute. "
                f"Instead received {logger!r}."
            )
        self.logger = logger
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
            # TODO: attempt digging into function **kwargs as well?
            # TODO: consider a configurable 'log_defaults' decorator parameter that will allow the logging of
            #  function definition defaults when those arguments aren't passed to the function
            mapped_args = inspect.signature(f).bind(*func_args, **func_kwargs).arguments

            for dec_param_name, param_config_entry in self.decorator_mapping.items():
                if dec_param_name not in mapped_args:
                    extra[param_config_entry.logger_name] = missing
                else:
                    value_candidate = mapped_args[dec_param_name]  # if not diggable, this will be the actual value
                    if param_config_entry.diggable:
                        extra[param_config_entry.logger_name] = _pluck_value(
                            value_candidate,
                            param_config_entry.dig_path,
                            delimiter=self.path_delimiter,
                        )
                    else:
                        extra[param_config_entry.logger_name] = value_candidate

            print("created logger dict", extra)

            with _CapturedLoggerAdapter(self.logger, extra):
                return f(*func_args, **func_kwargs)

        return wrapper
