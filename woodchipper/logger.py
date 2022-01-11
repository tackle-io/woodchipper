import os
from typing import Any, Mapping, Optional, Sequence

from structlog.stdlib import BoundLogger as StdlibBoundLogger

NO_PREFIX_LIST = ["exc_info"]


class BoundLogger(StdlibBoundLogger):
    def prefix_kwargs(self, **kwargs: Any) -> Mapping[str, Any]:
        prefix = os.getenv("WOODCHIPPER_KEY_PREFIX")
        if not prefix:
            return kwargs
        prefixed_kw = {}
        for key, value in kwargs.items():
            prefixed_kw[key if "." in key or key in NO_PREFIX_LIST else f"{prefix}.{key}"] = value
        return prefixed_kw

    def prefix_keys(self, *keys: str) -> Sequence[str]:
        prefix = os.getenv("WOODCHIPPER_KEY_PREFIX")
        if not prefix:
            return keys
        return [key if "." in key or key in NO_PREFIX_LIST else f"{prefix}.{key}" for key in keys]

    def bind(self, **new_values: Any) -> "BoundLogger":
        return super().bind(**self.prefix_kwargs(**new_values))  # type: ignore

    def unbind(self, *keys: str) -> "BoundLogger":
        return super().unbind(*self.prefix_keys(*keys))  # type: ignore

    def try_unbind(self, *keys: str) -> "BoundLogger":
        return super().try_unbind(*self.prefix_keys(*keys))  # type: ignore

    def _proxy_to_logger(
        self, method_name: str, event: Optional[str] = None, *event_args: str, **event_kw: Any
    ) -> Any:
        return super()._proxy_to_logger(method_name, event, *event_args, **self.prefix_kwargs(**event_kw))
