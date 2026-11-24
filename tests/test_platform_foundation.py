import pytest

from app_base.core.idempotency import IdempotencyRecord, replay_or_none, request_hash
from app_base.core.service_scopes import required_scopes
from app_base.integrations.auth import ServiceCredential, s2s_headers


class MemoryIdempotency:
    def __init__(self):
        self.records = {}

    async def get(self, key):
        return self.records.get(key)

    async def save(self, record):
        self.records[record.key] = record


@pytest.mark.asyncio
async def test_idempotency_replays_same_body_and_rejects_conflict():
    store = MemoryIdempotency()
    body = {"amount": 1200, "currency": "XAF"}
    await store.save(IdempotencyRecord("checkout-1", request_hash(body), 201, {"ok": True}))
    assert (await replay_or_none(store, "checkout-1", body)).response_body == {"ok": True}
    with pytest.raises(Exception):
        await replay_or_none(store, "checkout-1", {"amount": 999, "currency": "XAF"})


def test_service_scopes_are_isolated_and_headers_are_explicit():
    assert "diddipay:payment-intents:write" in required_scopes("diddipay")
    assert "diddisend:deliveries:write" in required_scopes("diddisend")
    assert "diddisend:deliveries:write" not in required_scopes("diddipay")
    headers = s2s_headers(
        ServiceCredential(service="diddisend", client_id="diddishop", access_token="token"),
        origin_service="diddishop",
        user_id="diddishop-system",
        request_id="req-1",
        idempotency_key="shop:create-delivery:order-1:1",
    )
    assert headers["Authorization"] == "Bearer token"
    assert headers["X-Origin-Service"] == "diddishop"
    assert headers["Idempotency-Key"].startswith("shop:create-delivery:")
