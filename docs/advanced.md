---
title: Advanced Usage
description: Using more advanced features of Woodchipper
weight: 20
---

## Naming a LoggingContext

When a `LoggingContext` exits, it emits a log message saying so. That message includes the module and function in
which the `LoggingContext` was defined. You may want to customize that name to something more understandable. To do
this, provide a single positional argument to `LoggingContext` when you define it. That name will be used instead.

```python
with LoggingContext("custom-name", user=request.user.id):
```

When this context exits, the message will use the custom name instead of the module and function name.

```python
2022-01-20 10:49.54 [info     ] Exiting context: custom-name [woodchipper.context] context.time_to_run_musec=1318 func_name=<module> lineno=1 module=<stdin> user=1000
```

## Namespacing context variables with a prefix

Woodchipper supports organizing the keys of a structured log message into namespaces, separated the namespace prefix
from the key name by a `.`.

You can set the default namespace for all contextual logging keys you set in your application by setting the
environment variable `WOODCHIPPER_KEY_PREFIX` to the prefix value. For example, if you set `WOODCHIPPER_KEY_PREFIX` to
`tackle` and emitted a log message like `logger.info("Message", data=100)`, the output would append the prefix to the
key name, so it became `tackle.data` instead of simply `data`.

You can also set the prefix on a `LoggingContext`, overriding the default key prefix, with the `_prefix` kwarg. For
example:

```python
with LoggingContext(user=request.user.id, _prefix="demo"):
    logging.info("Demo beginning.")
```

In the above message, the `user` contextual key would be outputted as `demo.user`, regardless of the value of the
`WOODCHIPPER_KEY_PREFIX` environment variable.

## Changing context logging levels

Woodchipper supports changing the log level of entrance and exit logging for contexts, with the default log level of `"INFO"`.

You can set the default log level for all context logs by setting the environment variable `WOODCHIPPER_CONTEXT_LOG_LEVEL` to
the desired log level name. For example, if you set `WOODCHIPPER_CONTEXT_LOG_LEVEL` to `"DEBUG"` all logs created when entering or
exiting a LoggingContext would be debug by default.

You can also set the log level on a `LoggingContext`, overriding the default log level, with the `_log_level` kwarg. For
example:

```python
with LoggingContext(user=request.user.id, _log_level="ERROR"):
    logger.info("Demo beginning.")
```

In the above message, the entrance and exit logs would be outputted as level `"ERROR"`, regardless of the value of the
`WOODCHIPPER_CONTEXT_LOG_LEVEL` environment variable. Examples of the output logs can be seen here:

```
2024-02-02T15:44:48.488489 [error    ] Entering context: __main__:<module> [__main__] func_name=<module> lineno=1 module=demo tkl.context_name=__main__:<module> tkl.user=user-123
2024-02-02T15:44:48.488805 [info     ] Demo beginning.      [__main__] func_name=<module> lineno=2 module=demo tkl.user=user-123
2024-02-02T15:44:48.489311 [error    ] Exiting context: __main__:<module> [__main__] context.time_to_run_musec=859 func_name=<module> lineno=1 module=demo tkl.context_name=__main__:<module> tkl.user=user-123
```

## Using Woodchipper with Flask

Woodchipper ships with a built-in Flask integration, which wraps the entire request/response cycle in a
`LoggingContext`, which adds headers and other basic request information to the context, including a unique ID for
each request. Each of the keys in the context added by this integration will be prefixed with `http`.

To enable the Flask integration, you have to modify the `Flask` app isntance. This is non-standard versus other Flask
extensions, where you simply wrap the Flask object.

```python
from flask import Flask
from woodchipper.http.flask import WoodchipperFlask

app = Flask(__name__)
flask.WoodchipperFlask(app).chipperize()
```

The Flask integration's logging context is emitted on the `woodchipper.http.flask` named facility with `INFO` priority,
so you'll want to make sure your logging configuration includes such messages.

The `WoodchipperFlask` constructor also takes an optional kwarg parameter `request_id_factory`. By passing to this
parameter an argumentless callable, you can customize how the unique request ID is generated.

## Using Woodchipper with FastAPI

Woodchipper ships with a built-in FastAPI integration, which wraps the entire request/response cycle in a
`LoggingContext`, which adds headers and other basic request information to the context, including a unique ID for
each request. Each of the keys in the context added by this integration will be prefixed with `http`.

To enable the FastAPI integration, you have to modify the `FastAPI` app instance.

There are two ways to do this. The first, chipperize() is the recommended approach to get accurate timing data
in most cases-- it ensures the Woodchipper middleware is the first in the middleware stack.
However, if you also have Datadog's DDTrace middleware installed on the same application, chipperize may cause
tracing to break. In those cases, manual installation (see second example) is preferred.

Chipperize:
```python
from fastapi import FastAPI
from woodchipper.http.fastapi import WoodchipperFastAPI

app = FastAPI()
WoodchipperFastAPI(app).chipperize()
```

Manual installation:
```python
from fastapi import FastAPI
from woodchipper.http.fastapi import WoodchipperFastAPI

app = FastAPI()
app.add_middleware(WoodchipperFastAPI)
```

The middleware's logging context is emitted on the `woodchipper.http.fastapi` named facility with `INFO` priority,
 so you'll want to make sure your logging configuration includes such messages.

The `WoodchipperFastAPI` constructor also takes an optional kwarg parameter `request_id_factory`. By passing to this
parameter an argumentless callable, you can customize how the unique request ID is generated.


## Using Woodchipper with AWS Lambda

Woodchipper ships with a built-in AWS Lambda integration when using [Zappa](https://github.com/Zappa/zappa), which
wraps the entire Lambda dispatch cycle in a `LoggingContext`, adding to the context information about the Lambda
execution environment. Each of the keys in the context added by this integration will be prefixed with `lambda`.

To enable the Lambda integration, you have to use it like a WSGI middleware.

```python
# Let's say your WSGI callable is named app
from woodchipper.http.awslambda import WoodchipperLambda

app = WoodchipperLambda(app)

# If you're using Flask, wrapping the WSGI callable looks like this

from flask import Flask

app = Flask(__name__)
app.wsgi_app = WoodchipperLambda(app.wsgi_app)
```

## Using Woodchipper with Sentry
There is an optional dependency for [structlog-sentry](https://github.com/kiwicom/structlog-sentry) that can be installed
using `pip install woodchipper[sentry]`. If you're using the `JSONLogToStdout` configuration and have the optional dependency installed, Woodchipper will handle emitting error-level log
messages from your application to Sentry. You are still responsible for configuring the Sentry SDK yourself.

**NOTE** As of right now we do not support structlog-sentry >= 2.0.0. If you installed `structlog-sentry` before it was added
as an optional dependency make sure you have it pinned to a version below 2.0.0.
