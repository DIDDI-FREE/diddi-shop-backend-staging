from urllib.parse import parse_qs

import httpx
import pytest

from app_base.integrations.auth import ServiceCredential, ServiceTokenProvider, s2s_headers_async


@pytest.mark.asyncio
async def test_client_credentials_is_cached_per_target_and_scope():
    calls: list[dict] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = {key: values[0] for key, values in parse_qs(request.content.decode()).items()}
        calls.append({"url": str(request.url), "headers": dict(request.headers), "body": body})
        return httpx.Response(200, json={"access_token": f"token-{body['audience']}", "expires_in": 600})

    transport = httpx.MockTransport(handler)
    provider = ServiceTokenProvider(
        token_url="https://auth.test/identity/v1/auth/service/token",
        client_id="diddishop-staging-diddipay",
        client_secret="secret-pay",
        audience="diddipay",
        scopes=("diddipay:payment-intents:write", "diddipay:payment-intents:refund"),
        transport=transport,
    )

    first = await provider.access_token()
    second = await provider.access_token()

    assert first == second == "token-diddipay"
    assert len(calls) == 1
    assert calls[0]["headers"]["x-client-id"] == "diddishop-staging-diddipay"
    assert calls[0]["body"]["grant_type"] == "client_credentials"
    assert calls[0]["body"]["scope"] == "diddipay:payment-intents:write diddipay:payment-intents:refund"


@pytest.mark.asyncio
async def test_target_credential_sends_bearer_and_client_id():
    provider = ServiceTokenProvider(
        token_url="https://auth.test/identity/v1/auth/service/token",
        client_id="diddishop-staging-diddisend",
        client_secret="secret-send",
        audience="diddisend",
        scopes=("diddisend:deliveries:create",),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"access_token": "send-token", "expires_in": 600})
        ),
    )

    headers = await s2s_headers_async(
        ServiceCredential(
            service="diddisend",
            client_id="diddishop-staging-diddisend",
            scopes=("diddisend:deliveries:create",),
            token_provider=provider,
        ),
        idempotency_key="shop:create-delivery:order-1:1",
    )

    assert headers["Authorization"] == "Bearer send-token"
    assert headers["X-Client-ID"] == "diddishop-staging-diddisend"
    assert headers["Idempotency-Key"] == "shop:create-delivery:order-1:1"
