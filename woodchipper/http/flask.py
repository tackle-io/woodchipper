import uuid

from flask import g, request

from woodchipper.context import LoggingContext

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
                "url": request.url,
                **{
                    f"header.{header.lower()}": ("******" if header.lower() in self._blacklisted_headers else value)
                    for header, value in request.headers.items()
                },
            },
            _prefix="http",
        ):
            return self.vanilla_full_dispatch_request()

    def chipperize(self):
        self._app.full_dispatch_request = self.wrapped_full_dispatch_request
