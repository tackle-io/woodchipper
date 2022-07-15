import time
from typing import Callable, Optional

from sqlalchemy import engine, event

from woodchipper.monitors import BaseMonitor


class SQLAlchemyMonitor(BaseMonitor):
    statement_count: int
    last_statement_started_at: Optional[float]
    total_db_time: float
    engine: engine.Engine
    instance_setup_cb: Optional[Callable]

    def __init__(self):
        self.statement_count = 0
        self.last_statement_started_at = None
        self.total_db_time = 0.0

    def handle_before_event(self, conn, cursor, statement, parameters, context, executemany):
        self.last_statement_started_at = time.time()

    def handle_after_event(self, conn, cursor, statement, parameters, context, executemany):
        assert self.last_statement_started_at
        exec_time = time.time() - self.last_statement_started_at
        self.last_statement_started_at = None
        self.total_db_time += exec_time
        self.statement_count += 1

    def setup(self):
        if self.instance_setup_cb is not None:
            self.instance_setup_cb()
        event.listen(self.engine, "before_cursor_execute", self.handle_before_event)
        event.listen(self.engine, "after_cursor_execute", self.handle_after_event)

    def finish(self):
        event.remove(self.engine, "before_cursor_execute", self.handle_before_event)
        event.remove(self.engine, "after_cursor_execute", self.handle_after_event)
        return {"sql.statement_count": self.statement_count, "sql.total_db_time_musec": int(self.total_db_time * 1e6)}
