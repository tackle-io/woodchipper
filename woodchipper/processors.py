import json
import logging
from typing import Union, Mapping, Tuple, Type

from structlog import DropEvent

from woodchipper import context, get_facilities


def inject_context_processor(logger: logging.Logger, method: str, event_dict: dict):
    """
    A function to update context with new log event key/value
    Returns updated context items
    """
    ctx_items = context.logging_ctx.as_dict()
    ctx_items.update(event_dict)

    return ctx_items


class GitVersionProcessor:
    """
    Loads the contents of a static file written during CI builds with the git revision info.
    """

    def __init__(self, version_json_path="version.json"):
        self.version_json_path = version_json_path

    def __call__(self, logger: logging.Logger, method: str, event_dict: dict):
        try:
            with open(self.version_json_path) as ifs:
                git_version = json.load(ifs)
                event_dict.update({f"git.{k}": v for k, v in git_version.items()})
        except (OSError, json.JSONDecodeError):
            pass
        return event_dict


NameFacilityPair = Tuple[str, str]

NoMatch = None


def _match_name_to_closest_facility(
    dot_delimited_full_name: str, mapping: Mapping[str, str]
) -> Union[NameFacilityPair, NoMatch]:

    matches = []
    if not mapping:
        return NoMatch
    for candidate in mapping.keys():
        if dot_delimited_full_name.startswith(candidate):
            matches.append(candidate)

    if not matches:
        return NoMatch

    matches.sort(key=lambda elem: len(elem))
    return matches[-1], mapping[matches[-1]]


_EventDict = Type["T"]


def minimum_log_level_processor(logger, method_name, event_dict: _EventDict) -> _EventDict:
    facility_match = _match_name_to_closest_facility(logger.name, get_facilities())
    if facility_match:
        _facility, facility_log_level = facility_match
        if logging.getLevelName(method_name.upper()) < logging.getLevelName(facility_log_level):
            raise DropEvent
    else:
        # No match, so no filtering -- allow it through until we implement a default
        pass

    return event_dict
