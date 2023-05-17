import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from woodchipper.context import LoggingContext, logging_ctx

BLACKLISTED_HEADERS = ["authorization", "cookie"]


class WoodchipperFastAPI(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        request_id_factory=None,
        blacklisted_headers=BLACKLISTED_HEADERS,
    ):
        super().__init__(app)
        self._app = app
        self._blacklisted_headers = blacklisted_headers
        self._request_id_factory = request_id_factory or (lambda: str(uuid.uuid4()))

    def _wrap_build_middleware_stack(self, original_fn):
        def __wrapped__():
            fastapi_app = original_fn()
            return WoodchipperFastAPI(
                app=fastapi_app,
                blacklisted_headers=self._blacklisted_headers,
                request_id_factory=self._request_id_factory,
            )

        return __wrapped__

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # When the request object parses query params it doesn't combine repeat
        # params into a list. This doesn't happen until FastAPI is preparing to
        # call the handling function. We do want to see repeat params as a list so
        # we combine them here.
        queries = {}
        for k, v in request.query_params.multi_items():
            if k in queries and not isinstance(queries[k], list):
                queries[k] = [queries[k], v]
            elif k in queries:
                queries[k].append(v)
            else:
                queries[k] = v

        with LoggingContext(
            "fastapi:request",
            **{
                "id": self._request_id_factory(),
                "body_size": int(request.headers.get("content-length", 0)),
                "method": request.method,
                "path": request.base_url._url,
                **{f"query_param.{k.lower()}": v for k, v in queries.items()},
                **{
                    f"header.{k.lower()}": (v if k.lower() not in self._blacklisted_headers else "******")
                    for k, v in request.headers.items()
                },
            },
            _prefix="http",
        ):
            try:
                response: Response = await call_next(request)
            except Exception as e:
                logging_ctx.update({"http.response.status_code": 500})
                raise e
            else:
                logging_ctx.update(
                    {
                        "http.response.status_code": response.status_code,
                        "http.response.content_length": int(response.headers.get("content-length", 0)),
                    }
                )

                return response

    def chipperize(self):
        self._app.build_middleware_stack = self._wrap_build_middleware_stack(self._app.build_middleware_stack)
