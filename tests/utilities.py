from logging import LoggerAdapter
from typing import Any, MutableMapping


class InspectableLoggerAdapter(LoggerAdapter):
    def __init__(self, *args, **kwargs):
        self.logged_messages = []
        super().__init__(*args, **kwargs)

    def process(self, msg, kwargs):
        self.logged_messages.append((msg, kwargs))
        return msg, kwargs


class SimpleLoggerAdapterInterface:
    """Minimum interface"""

    def __init__(self, extra):
        self.extra = extra
