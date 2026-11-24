from typing import Any

import httpx

from app_base.core.errors import NotConfiguredError
from app_base.integrations.auth import ServiceCredential, s2s_headers_async


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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.request(method, self._url(path), headers=merged_headers, **kwargs)
