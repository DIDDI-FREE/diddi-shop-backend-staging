import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from time import monotonic

from opentelemetry import trace

from app_base.core.request_context import get_request_context
from app_base.core.telemetry import MAX_EVENT_BYTES, resource_attributes

logger = logging.getLogger("diddi_shop")

_REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "pin",
    "otp",
    "token",
    "cookie",
    "api_key",
    "apikey",
    "authorization",
    "secret",
    "signed_url",
    "signature",
    "body",
    "request",
    "response",
    "headers",
    "payment",
    "card",
    "cvv",
    "phone",
    "email",
    "address",
    "latitude",
    "longitude",
    "location",
    "ip",
)


def _sanitize(value: object, key: str = "") -> object:
    normalized_key = key.lower().replace("-", "_")
    if any(part in normalized_key for part in _SENSITIVE_KEY_PARTS):
        return _REDACTED
    if isinstance(value, dict):
        return {str(child_key): _sanitize(child_value, str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item, key) for item in value]
    if isinstance(value, str):
        if normalized_key in {"url", "uri", "endpoint"} and any(
            marker in value.lower() for marker in ("signature=", "x-amz-", "token=", "expires=")
        ):
            return _REDACTED
        return value[:MAX_EVENT_BYTES]
    return value


def _trace_fields() -> dict[str, str]:
    context = trace.get_current_span().get_span_context()
    if not context.is_valid:
        return {}
    trace_id = format(context.trace_id, "032x")
    span_id = format(context.span_id, "016x")
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "traceparent": f"00-{trace_id}-{span_id}-01",
    }


def log_event(name: str, **fields: object) -> None:
    context = get_request_context()
    message = str(fields.pop("message", name))
    payload: dict[str, object] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": str(fields.pop("level", "INFO")),
        "event": name,
        "message": message[:MAX_EVENT_BYTES],
        "resource": resource_attributes(),
        **_sanitize(fields),
    }
    if context:
        payload.update(request_id=context.request_id, correlation_id=context.correlation_id)
    payload.update(_trace_fields())
    serialized = json.dumps(payload, default=str, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > MAX_EVENT_BYTES:
        compact_payload = {
            key: payload[key]
            for key in ("timestamp", "level", "event", "message", "resource", "request_id", "correlation_id", "trace_id", "span_id", "traceparent")
            if key in payload
        }
        compact_payload["details_truncated"] = True
        serialized = json.dumps(compact_payload, default=str, separators=(",", ":"))
    logger.info("%s", serialized)


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
