import inspect
from functools import wraps
from typing import Mapping, NamedTuple, Tuple, Union, Any

from woodchipper.context import LoggingContext, _convert_to_loggable_value


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
    logger_name: str
    diggable: bool


def _build_path_head_to_param_config_map(kwargs: Mapping, *, delimiter: str = ".") -> Mapping[str, ParamSearchConfig]:
    return_mapping = {}
    for logger_name, dig_path in kwargs.items():
        if dig_path == "":
            raise ValueError("Dig path cannot be an empty string")

        dig_path_head, dig_path_tail = _split_head_node(dig_path, delimiter)

        return_mapping[dig_path_head] = ParamSearchConfig(
            dig_path=dig_path_tail,
            logger_name=logger_name,
            diggable=True if dig_path_tail else False,
        )

    return return_mapping


class arg_logger:
    def __init__(self, *, missing_default=missing, path_delimiter=".", **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs
        self.missing_default = missing_default
        self.path_delimiter = path_delimiter
        self.decorator_mapping = _build_path_head_to_param_config_map(decorator_kwargs, delimiter=path_delimiter)

    def __call__(self, f):
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

            values_to_inject_into_ctx = {}

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

                values_to_inject_into_ctx[param_config_entry.logger_name] = _convert_to_loggable_value(raw_value)

            with LoggingContext(values_to_inject_into_ctx):
                return f(*func_args, **func_kwargs)

        return wrapper
