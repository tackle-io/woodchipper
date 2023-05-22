import uuid
from typing import Callable

from fastapi import FastAPI, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from woodchipper.context import LoggingContext, logging_ctx

BLACKLISTED_HEADERS = ["authorization", "cookie"]


class WoodchipperFastAPI:
    def __init__(
        self,
        app: FastAPI,
        request_id_factory=None,
        blacklisted_headers=BLACKLISTED_HEADERS,
    ):
        self._app = app
        self._blacklisted_headers = blacklisted_headers
        self._request_id_factory = request_id_factory or (lambda: str(uuid.uuid4()))

    def _wrap_build_middleware_stack(self, original_fn: Callable) -> Callable:
        def __wrapped__() -> ASGIApp:
            asgi_app = original_fn()
            return WoodchipperFastAPI(
                app=asgi_app,
                blacklisted_headers=self._blacklisted_headers,
                request_id_factory=self._request_id_factory,
            )

        return __wrapped__

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # When the request object parses query params it doesn't combine repeat
        # params into a list. This doesn't happen until FastAPI is preparing to
        # call the handling function. We do want to see repeat params as a list so
        # we combine them here.
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        request = Request(scope)
        queries = {}
        for k, v in request.query_params.multi_items():
            if k in queries and not isinstance(queries[k], list):
                queries[k] = [queries[k], v]
            elif k in queries:
                queries[k].append(v)
            else:
                queries[k] = v

        async def send_with_extra_headers(message):
            if message["type"] == "http.response.start":
                logging_ctx.update(
                    {
                        "http.response.status_code": message["status"],
                        "http.response.content_length": int(dict(message["headers"]).get(b"content-length", 0)),
                    }
                )
            return await send(message)

        with LoggingContext(
            "fastapi:request",
            **{
                "id": self._request_id_factory(),
                "body_size": int(request.headers.get("content-length", 0)),
                "method": request.method,
                "path": str(request.base_url)[:-1] + request.url.path if request.url.path else request.base_url,
                **{f"query_param.{k.lower()}": v for k, v in queries.items()},
                **{
                    f"header.{k.lower()}": (v if k.lower() not in self._blacklisted_headers else "******")
                    for k, v in request.headers.items()
                },
            },
            _prefix="http",
        ):
            try:
                await self._app(scope, receive, send_with_extra_headers)
            except Exception:
                logging_ctx.update({"http.response.status_code": 500})
                raise

    def chipperize(self):
        self._app.build_middleware_stack = self._wrap_build_middleware_stack(self._app.build_middleware_stack)
