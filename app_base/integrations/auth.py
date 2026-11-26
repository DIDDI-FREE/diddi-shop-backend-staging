from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class ServiceTokenProvider:
    """Fetch and cache one DiddiFreeID client-credentials token per target."""

    token_url: str
    client_id: str
    client_secret: str
    audience: str
    scopes: tuple[str, ...] = ()
    timeout_seconds: float = 10.0
    transport: httpx.AsyncBaseTransport | None = None
    _cached: tuple[str, float] | None = field(default=None, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    async def access_token(self) -> str:
        now = time.monotonic()
        if self._cached and now < self._cached[1]:
            return self._cached[0]

        async with self._lock:
            now = time.monotonic()
            if self._cached and now < self._cached[1]:
                return self._cached[0]
            if not self.token_url or not self.client_id or not self.client_secret:
                raise ValueError(f"Incomplete client-credentials configuration for {self.audience}")
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                    response = await client.post(
                        self.token_url,
                        headers={"X-Client-ID": self.client_id},
                        data={
                            "grant_type": "client_credentials",
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "audience": self.audience,
                            "scope": " ".join(self.scopes),
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                token = payload["access_token"]
                if not isinstance(token, str) or not token:
                    raise ValueError("token response does not contain access_token")
                expires_in = max(int(payload.get("expires_in", 600)), 1)
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"Unable to acquire DiddiFreeID token for {self.audience}") from exc

            self._cached = (token, time.monotonic() + max(expires_in - 30, 1))
            return token


@dataclass(frozen=True)
class ServiceCredential:
    service: str
    client_id: str
    access_token: str | None = None
    service_key: str | None = None
    scopes: tuple[str, ...] = ()
    token_provider: ServiceTokenProvider | None = None
    origin_service: str = "diddishop"
    user_id: str = "diddishop-system"


def s2s_headers(
    credential: ServiceCredential,
    *,
    origin_service: str | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    headers = {
        "X-Origin-Service": origin_service or credential.origin_service,
        "X-User-ID": user_id or credential.user_id,
    }
    if credential.access_token:
        headers["Authorization"] = f"Bearer {credential.access_token}"
        headers["X-Client-ID"] = credential.client_id
    elif credential.service_key:
        headers["X-Client-ID"] = credential.client_id
        headers["X-Service-Key"] = credential.service_key
    else:
        raise ValueError(f"No S2S credential configured for {credential.service}")
    if request_id:
        headers["X-Request-ID"] = request_id
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    if credential.scopes:
        headers["X-Service-Scopes"] = " ".join(credential.scopes)
    return headers


async def s2s_headers_async(
    credential: ServiceCredential,
    *,
    origin_service: str | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """Build headers, obtaining a short-lived token when configured."""
    if credential.token_provider is not None:
        token = await credential.token_provider.access_token()
        return s2s_headers(
            ServiceCredential(
                service=credential.service,
                client_id=credential.client_id,
                access_token=token,
                service_key=credential.service_key,
                scopes=credential.scopes,
                origin_service=credential.origin_service,
                user_id=credential.user_id,
            ),
            origin_service=origin_service,
            user_id=user_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
    return s2s_headers(
        credential,
        origin_service=origin_service,
        user_id=user_id,
        request_id=request_id,
        idempotency_key=idempotency_key,
    )
