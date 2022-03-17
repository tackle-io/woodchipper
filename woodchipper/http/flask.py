import uuid

from flask import g, request

from woodchipper.context import LoggingContext, logging_ctx

BLACKLISTED_HEADERS = ["authorization", "cookie"]


class WoodchipperFlask:
    def __init__(self, app, blacklisted_headers=BLACKLISTED_HEADERS, request_id_factory=None):
        self._app = app
        self._blacklisted_headers = blacklisted_headers
        self._request_id_factory = request_id_factory or (lambda: str(uuid.uuid4()))
        self.vanilla_full_dispatch_request = app.full_dispatch_request

    def wrapped_full_dispatch_request(self):
        if not getattr(g, "request_id", None):
            g.request_id = self._request_id_factory()
        with LoggingContext(
            "flask:request",
            **{
                "id": g.request_id,
                "body_size": request.content_length,
                "method": request.method,
                "path": request.base_url,
                **{
                    f"query_param.{param_key.lower()}": param_val_list[0]
                    if len(param_val_list) == 1
                    else param_val_list
                    for param_key, param_val_list in request.args.lists()
                },
                **{
                    f"header.{header.lower()}": ("******" if header.lower() in self._blacklisted_headers else value)
                    for header, value in request.headers.items()
                },
            },
            _prefix="http",
        ):

            try:
                response = self.vanilla_full_dispatch_request()
            except Exception:
                # non HTTPErrors will not be caught by flask, so if that's
                # happening we assume that it's crashing the response and
                # thus 500 level
                logging_ctx.update(
                    {
                        "http.response.status_code": 500,
                    }
                )
                raise
            else:

                logging_ctx.update(
                    {
                        "http.response.status_code": response.status_code,
                        "http.response.content_length": response.content_length,
                    }
                )
                return response

    def chipperize(self):
        self._app.full_dispatch_request = self.wrapped_full_dispatch_request
