---
title: Monitors
description: A monitor class allows you to enhance the functionality and output of `LoggingContext`
---

A monitor class adds additional measurement and context to a `LoggingContext`. As part of the call to
`woodchipper.configure`, you can specify what monitors should be in effect for your application.

## BaseMonitor

Every monitor class subclasses the `BaseMonitor` class and implements its contract. The `BaseMonitor` is simply:

```python
from typing import Dict

from woodchipper.context import LoggableValue


class BaseMonitor:
    def __init__(self):
        raise NotImplementedError()

    def setup(self):
        raise NotImplementedError()

    def finish(self) -> Dict[str, LoggableValue]:
        raise NotImplementedError()
```

The `setup()` method is called while entering a new `LoggingContext`, and the `finish()` method is called when
exiting. The return value from `finish()` is any additional key/value pairs that should be included in the log
message emitted when exiting the context.

You may implement and configure custom monitors for your application, so long as they subclass `BaseMonitor` and
complete the contract it outlines.

## Example: SQLAlchemyMonitor

Woodchipper ships with a monitor class for tracking the database access of code executed in a `LoggingContext`. It
requires a callback be defined to access the SQLAlchemy engine.

```python
import os

import sqlalchemy
import woodchipper
import woodchipper.configs
from woodchipper.monitors.sqlalchemy import SQLAlchemyMonitor

engine = sa.create_engine(os.getenv("DATABASE_DSN"))

def sa_callback(sa_monitor)):
    sa_monitor.engine = engine

SQLAlchemyMonitor.instance_setup_cb = sa_callback

woodchipper.configure(
    config=woodchipper.configs.JSONLogToStdout,
    facilities={"": "INFO"},
    monitors=[SQLAlchemyMonitor])
```

With this monitor configured and installed, whenever a `LoggingContext` exits and emits the log message noting the
exit, it will include two additional keys in that exit log message:

* `sql.statement_count` - the number of SQL statements executed during that context
* `sql.total_db_time_musec` - the number of microseconds spent transacting with the database during that context
