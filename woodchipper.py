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
    path: str
    logger_name: str
    diggable: bool


def _build_path_head_to_param_config_map(kwargs: Mapping, *, delimiter: str = '.') -> Mapping[str, ParamSearchConfig]:
    return_mapping = {}
    for logger_name, dig_path in kwargs.items():
        if dig_path == '':
            raise ValueError("Dig path cannot be an empty string")
        dig_head, *remaining_dig_parts = dig_path.split(delimiter)
        return_mapping[dig_head] = ParamSearchConfig(
            path=dig_path,
            logger_name=logger_name,
            diggable=True if remaining_dig_parts else False
        )

    return return_mapping


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
            # breakpoint()
            for arg in func_args:
                if arg in self.decorator_mapping:
                    config = self.decorator_mapping[arg]
                    if not config.diggable:
                        extra[config.logger_name] = arg
                    else:
                        extra[config.logger_name] = _pluck_value(arg, config.path, delimiter=self.path_delimiter)

            for kwarg_key, kwarg_value in func_kwargs.items():
                if kwarg_key in self.decorator_mapping:
                    config = self.decorator_mapping[kwarg_key]
                    if not config.diggable:
                        extra[config.logger_name] = kwarg_value
                    else:
                        _discarded_head, search_path = _split_head_node(config.path)
                        extra[config.logger_name] = _pluck_value(kwarg_value, search_path, delimiter=self.path_delimiter)

            print("created logger dict", extra)

            return f(*func_args, **func_kwargs)

        return wrapper
