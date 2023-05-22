---
title: Basic Usage
description: A thorough look at how to use Woodchipper for logging
weight: 10
---

Woodchipper has a range of features that make emitting contextually-aware, structured log messages easier and
more complete.

## Configuring Woodchipper

Set up Woodchipper by calling `woodchipper.configure` as early in your code as you can. It wraps `structlog` and the
Python standard library logger, disabling other loggers you might have configured.

The `configure` function takes a number of optional keyword arguments.

* `config` is a configuration class that outlines the structlog configuration you want to use. There are pre-baked
  configuration classes in `woodchipper.configs` you can use: `DevLogToStdout` is for developer environments and
  `JSONLogToStdout` is for production environments. `Minimal` is also present but primarily used for Woodchipper's
  internal tests.
* `facilities` is a Python dictionary for configuring what logging facilities to capture logging output from. Even if
  a library doesn't use Woodchipper for its logging, Woodchipper can emit logs from that library as structured
  messages.

  The keys of `facilities` are the logging facility to capture -- usually the Python module name, since
  it's standard practice to use `__name__` as the name of the logger. The values of keys in `facilities` are the
  string names of the standard logging levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Loggers are
  configured to not [propagate](https://docs.python.org/3/library/logging.html#logging.Logger.propagate).

  For example, a valid value of `facilities` might be: `{"requests": "WARNING", "": "INFO"}`, which would configure
  the root logger to handle all messages at `INFO` level or above, unless the message was emitted from the
  `requests` library, in which case, only messages at `WARNING` or above will be handled.
* `override_existing` (default: `True`) determines whether the logging configuration will disable existing loggers
  or not.
* `monitors` is a list of [monitor]({{../monitors}}) that you want enabled on the logger.

## Getting a logger

To get a logger, use `woodchipper.get_logger` instead of `logging.getLogger`. The `get_logger` function requires a
string argument for the logger name.

## Adding context to a log message

The power of structured logging context from providing context for the logging event in the form of key/value
pairings. Those keys and values can make searching through logs incredibly powerful and flexible, and they can
be used to create metrics and graphs, to create alarms, and to allow for machine learning around the events that
happen during the operation of your software.

### Context for a single log message

Every log message you emit has the possibility of adding context to it simply by adding them as kwargs. For example,
imagine you have defined an object `customer` with an attribute `id`. To log the customer ID along with the log
message, you might have a message like:

```python
logger.info("Customer logged in.", customer_id=customer.id)
```

With this log message, it's very easy to query your log management system for log messages with this same event,
because it's constant. Then you can group and count by `customer_id` values to count how often which customers are
logging in over time.

### Context within a function

In a given function, you may emit several log messages, and those messages may have the same elements in their
context data. Rather than repeat the same key/value arguments in each log message sent, Woodchipper lets you bind
those key/value pairs to the logger within the function. This is comparable to a
[LoggerAdapter](https://docs.python.org/3/library/logging.html#loggeradapter-objects) object from the Python standard
library logging.

```python
import woodchipper

logger = woodchipper.get_logger(__name__)

def view_function(request: HttpRequest) -> HttpResponse:
    local_logger = logger.bind(user=request.user.id)
    local_logger.info("View function starting.")
    # ... snip ...
    local_logger.info("View function complete.")
```

Each log message emitted using `local_logger` will contain the context variable `user` without needing to explicitly
include it in each log message.

### Context across functions

Some logging contexts may even be relevant to set across function calls or even across libraries. Rather than passing
around a logger instance you've `.bind()`'ed with that context or re-`.bind()`'ing that context in each function, you
can use `woodchipper.context.LoggingContext` to set context variables that follow across your entire codebase until
that context is exited. `LoggingContext` can be used as a context manager or as a decorator.

```python
# core.py
import woodchipper

logger = woodchipper.get_logger(__name__)

def awesome_business_logic(customer_id):
    logger.info("Starting core business logic.")
    # ... snip ...
    logger.info("Core business logic complete.")
    return result


# routes.py
import woodchipper
from woodchipper.context import LoggingContext

from . import core

logger = woodchipper.get_logger(__name__)

def route_handler(request, customer_id):
    with LoggingContext(user=request.user.id, customer=customer_id):
        result = core.awesome_business_logic(customer_id)
        return {"result": result}


@LoggingContext(user="request.user.id", customer="customer_id")
def route_handler(request, customer_id):
    result = core.awesome_business_logic(customer_id)
    return {"result": result}
```

Both of the implementations of `route_handler` are effectively equivalent. Any log messages emitted from anywhere,
including from `core.py`, will include it its context the key/value pairs passed to LoggingContext.

As a decorator, since the values of the key/value logging context pairs aren't available yet, the values for the
kwargs given to `LoggingContext` are strings, evaluated at runtime from the arguments given to the decorated function
to determine the logging context value. The `.` in the string expressions can represent either an attribute or key
access. For example, in the decorator, `"foo.bar"` could resolve to `foo.bar` or `foo["bar"]`.

Additionally, when the context ends, a log message is emitted indicating the `LoggingContext` has been exited, with
context key/value pairs that include the time it took to execute the code in that context as well as the output of
any [monitors](../monitors) you have configured. The output might look like:

```
2022-01-20 10:49.54 [info     ] Starting core business logic.  [demo_app.core] func_name=awesome_business_logic lineno=8 module=core customer=ACMECORP user=1000
2022-01-20 10:49.54 [info     ] Core business logic complete.  [demo_app.core] func_name=awesome_business_logic lineno=10 module=core customer=ACMECORP user=1000
2022-01-20 10:49.54 [info     ] Exiting context: demo_app.routes:route_handler [woodchipper.context] context.time_to_run_musec=5249 func_name=handle_request lineno=17 module=wsgi_app customer=ACMECORP user=1000
```
