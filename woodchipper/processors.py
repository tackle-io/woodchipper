import json
import logging

from woodchipper import context

_ddtrace_present = False
try:
    import ddtrace
    from ddtrace import tracer

    _ddtrace_present = True
except ImportError:
    pass


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


class DatadogTraceProcessor:
    """
    Adds Datadog trace information via the ddtrace library if it is installed
    """

    def __init__(self) -> None:
        pass

    def __call__(self, logger: logging.Logger, method: str, event_dict: dict) -> dict:
        # Adapted from
        # https://docs.datadoghq.com/tracing/other_telemetry/connect_logs_and_traces/python/#no-standard-library-logging
        if not _ddtrace_present:
            return event_dict

        # get correlation ids from current tracer context
        span = tracer.current_span()
        trace_id, span_id = (span.trace_id, span.span_id) if span else (None, None)

        # add ids to structlog event dictionary
        if trace_id:
            event_dict["dd.trace_id"] = str(trace_id)
        if span_id:
            event_dict["dd.span_id"] = str(span_id)

        # add the env, service, and version configured for the tracer
        if ddtrace.config.env:
            event_dict["dd.env"] = ddtrace.config.env
        if ddtrace.config.service:
            event_dict["dd.service"] = ddtrace.config.service
        if ddtrace.config.version:
            event_dict["dd.version"] = ddtrace.config.version

        return event_dict
