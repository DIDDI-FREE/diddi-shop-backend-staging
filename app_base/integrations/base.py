from typing import Any

import httpx
from opentelemetry import propagate, trace
from opentelemetry.trace import Status, StatusCode

from app_base.core.errors import NotConfiguredError
from app_base.integrations.auth import ServiceCredential, s2s_headers_async

_tracer = trace.get_tracer("diddishop.integrations")


class ServiceAdapter:
    def __init__(self, *, base_url: str, audience: str, timeout: float = 10.0, credential: ServiceCredential | None = None):
        self.base_url = base_url.rstrip("/")
        self.audience = audience
        self.timeout = timeout
        self.credential = credential

    def _url(self, path: str) -> str:
        if not self.base_url:
            raise NotConfiguredError(f"{self.audience} adapter is not configured")
        return f"{self.base_url}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, *, headers: dict[str, str] | None = None, **kwargs: Any) -> httpx.Response:
        merged_headers = dict(headers or {})
        if self.credential is not None:
            merged_headers = {**await s2s_headers_async(self.credential), **merged_headers}
        propagate.inject(merged_headers)
        with _tracer.start_as_current_span(f"{self.audience}.request") as span:
            span.set_attribute("diddi.target_service", self.audience)
            span.set_attribute("http.request.method", method.upper())
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, self._url(path), headers=merged_headers, **kwargs)
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR))
                raise
            span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            return response
