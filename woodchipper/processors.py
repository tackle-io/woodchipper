import json
import logging

from woodchipper import context


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
