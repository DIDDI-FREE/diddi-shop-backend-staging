from typing import Any

import httpx

from app_base.core.errors import NotConfiguredError


class ServiceAdapter:
    def __init__(self, *, base_url: str, audience: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.audience = audience
        self.timeout = timeout

    def _url(self, path: str) -> str:
        if not self.base_url:
            raise NotConfiguredError(f"{self.audience} adapter is not configured")
        return f"{self.base_url}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, *, headers: dict[str, str] | None = None, **kwargs: Any) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.request(method, self._url(path), headers=headers, **kwargs)
