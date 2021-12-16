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
