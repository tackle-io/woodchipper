from typing import Dict

from woodchipper.context import LoggableValue


class BaseMonitor:
    def __init__(self):
        raise NotImplementedError()

    def setup(self):
        raise NotImplementedError()

    def finish(self) -> Dict[str, LoggableValue]:
        raise NotImplementedError()
