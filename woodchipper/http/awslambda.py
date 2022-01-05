import os

from woodchipper.context import LoggingContext


class WoodchipperLambda:
    def __init__(self, app):
        self._app = app

    def __call__(self, environ, start_response):
        if "LAMBDA_TASK_ROOT" not in os.environ:
            # This is a decent sentinel for being in a Lambda environment
            return self._app(environ, start_response)
        context = environ.get("lambda.context", object())
        with LoggingContext(
            "awslambda:dispatch",
            **{
                "aws-request-id": getattr(context, "aws_request_id", None),
                "function-version": getattr(context, "function_version", None),
                "function-name": getattr(context, "function_name", None),
            },
            _prefix="lambda",
        ):
            return self._app(environ, start_response)
