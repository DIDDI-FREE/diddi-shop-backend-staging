import json

import httpx
import pytest

from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryCommand


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
