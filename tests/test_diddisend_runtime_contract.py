import json

import httpx
import pytest

from app_base.core.errors import DeliveryQuoteUnavailableError
from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryCommand


def _delivery_context() -> dict:
    return {
        "pickup_location": {"lat": 3.8, "lng": 11.5},
        "dropoff_location": {"lat": 3.9, "lng": 11.6},
    }


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [
    {"quoted_price": 700},
    {"quote": {"amount_minor": 700, "currency": "XOF"}},
    {"quote": {"amount": {"value": 700, "currency": "XOF"}}},
])
async def test_diddisend_adapter_normalizes_numeric_and_object_quotes(payload):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    adapter = DiddiSendAdapter(
        base_url="https://send.test",
        audience="diddisend",
        transport=httpx.MockTransport(handler),
    )

    assert await adapter.quote("shop-1", [{"product_id": "product-1", "declared_value": 1500}], _delivery_context()) == 700


@pytest.mark.anyio
async def test_diddisend_adapter_maps_downstream_quote_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, json={"error": "route metrics must be positive"})

    adapter = DiddiSendAdapter(
        base_url="https://send.test",
        audience="diddisend",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DeliveryQuoteUnavailableError):
        await adapter.quote("shop-1", [{"product_id": "product-1", "declared_value": 1500}], _delivery_context())


@pytest.mark.anyio
async def test_diddisend_adapter_serializes_integer_quote_as_contract_string():
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(201, json={"id": "delivery-1"})

    adapter = DiddiSendAdapter(
        base_url="https://send.test",
        audience="diddisend",
        transport=httpx.MockTransport(handler),
    )
    await adapter.create_delivery(
        DeliveryCommand(order_id="order-1", idempotency_key="delivery-1"),
        {
            "order_reference": "shop-order:order-1",
            "customer_user_id": "buyer-1",
            "recipient_name": "Buyer",
            "recipient_phone": "237000000000",
            "pickup_location": {"lat": 3.8, "lng": 11.5},
            "pickup_address": "pickup",
            "dropoff_location": {"lat": 3.9, "lng": 11.6},
            "dropoff_address": "dropoff",
            "package": {"label": "order-1"},
            "quoted_price": 500,
            "financial_breakdown": {"currency": "XOF"},
        },
    )

    assert captured
    assert json.loads(captured[0].content)["quoted_price"] == "500"
