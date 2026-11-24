from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    correlation_id: str
    actor_id: str | None = None
    actor_type: str = "system"
    trace_id: str | None = None
    span_id: str | None = None


_current_context: ContextVar[RequestContext | None] = ContextVar("diddi_shop_context", default=None)


def set_request_context(context: RequestContext) -> None:
    _current_context.set(context)


def get_request_context() -> RequestContext | None:
    return _current_context.get()
