from time import monotonic
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app_base.core.observability import log_event
from app_base.core.request_context import RequestContext, set_request_context


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = monotonic()
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id
        set_request_context(RequestContext(request_id=request_id, correlation_id=correlation_id))
        try:
            response = await call_next(request)
        except Exception:
            log_event(
                "http.request",
                message="request failed",
                method=request.method,
                status="error",
                duration_ms=round((monotonic() - started) * 1000),
            )
            raise
        route = request.scope.get("route")
        route_template = getattr(route, "path", None) or request.scope.get("path", "unknown")
        log_event(
            "http.request",
            message="request completed",
            method=request.method,
            route=route_template,
            status_code=response.status_code,
            duration_ms=round((monotonic() - started) * 1000),
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        return response
