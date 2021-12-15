import json
from woodchipper import context

def inject_context_processor(event_dict: dict):
    """ 
    A function to update context with new log event key/value
    Returns updated context items
    """
    ctx_items = dict(context.logging_ctx)
    print(ctx_items)
    ctx_items.update(event_dict)

    return ctx_items
