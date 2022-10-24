import uuid
from typing import Any, Callable, Coroutine

from fastapi import FastAPI, Request, Response

from woodchipper.context import LoggingContext, logging_ctx

BLACKLISTED_HEADERS = ["authorization", "cookie"]


class WoodchipperFastAPI:
    def __init__(self, app: FastAPI, blacklisted_headers=BLACKLISTED_HEADERS, request_id_factory=None):
        self._app = app
        self._blacklisted_headers = blacklisted_headers
        self._request_id_factory = request_id_factory or (lambda: str(uuid.uuid4()))

    def get_custom_route_handler(self, gen_id, blacklisted_headers):
        def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:

            original_route_handler = super(type(self), self).get_route_handler()

            async def woodchipper_route_handler(request: Request) -> Response:

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
                        "id": gen_id(),
                        "body_size": int(request.headers.get("content-length", 0)),
                        "method": request.method,
                        "path": request.base_url._url,
                        **{f"query_param.{k.lower()}": v for k, v in queries.items()},
                        **{
                            f"header.{k.lower()}": (v if k.lower() not in blacklisted_headers else "******")
                            for k, v in request.headers.items()
                        },
                    },
                    _prefix="http",
                ):
                    try:
                        response: Response = await original_route_handler(request)
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

            return woodchipper_route_handler

        return get_route_handler

    def get_logging_route_class(self):
        return type(
            "WoodChipperApiRoute",
            (
                self._app.router.route_class,
            ),  # This allows us to handle cases where the routeclass has already been replaced
            {"get_route_handler": self.get_custom_route_handler(self._request_id_factory, self._blacklisted_headers)},
        )

    def chipperize(self):
        self._app.router.route_class = self.get_logging_route_class()
