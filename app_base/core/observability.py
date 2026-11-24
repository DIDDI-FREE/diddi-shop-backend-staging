import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import monotonic

from app_base.core.request_context import get_request_context

logger = logging.getLogger("diddi_shop")


def log_event(name: str, **fields: object) -> None:
    context = get_request_context()
    payload = {"event": name, **fields}
    if context:
        payload.update(request_id=context.request_id, correlation_id=context.correlation_id)
    logger.info("%s", payload)


@contextmanager
def observe_operation(name: str, **fields: object) -> Iterator[None]:
    started = monotonic()
    try:
        yield
    except Exception:
        log_event(name, status="error", duration_ms=round((monotonic() - started) * 1000), **fields)
        raise
    else:
        log_event(name, status="ok", duration_ms=round((monotonic() - started) * 1000), **fields)
