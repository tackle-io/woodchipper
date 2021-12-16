from woodchipper.context import LoggingContext


class WoodchipperLambda:
    def __init__(self, app):
        self._app = app

    def __call__(self, environ, start_response):
        if "LAMBDA_TASK_ROOT" not in environ:
            # This is a decent sentinel for being in a Lambda environment
            return self._app(environ, start_response)
        with LoggingContext(
            {"aws-request-id": getattr(environ.get("lambda.context", object()), "aws_request_id", None)},
            prefix="lambda",
        ):
            return self._app(environ, start_response)
