import json

import httpx
import pytest

from app_base.integrations.auth import ServiceCredential
from app_base.integrations.diddipay import DiddiPayAdapter
from app_base.shared_kernel.contracts.payments import PaymentIntentCommand


def test_diddipay_adapter_exposes_payment_lifecycle_without_card_data():
    assert hasattr(DiddiPayAdapter, "create_payment_intent")
    assert hasattr(DiddiPayAdapter, "cancel_payment_intent")
    assert hasattr(DiddiPayAdapter, "refund")
    assert not hasattr(DiddiPayAdapter, "charge_card")


@pytest.mark.anyio
async def test_diddipay_adapter_maps_shop_minor_units_to_staging_contract():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={"id": "00000000-0000-0000-0000-000000000001", "amount": 1500})

    adapter = DiddiPayAdapter(
        base_url="https://pay.test/payfund/v1",
        audience="diddipay",
        credential=ServiceCredential(service="diddipay", client_id="shop-pay", access_token="token"),
        transport=httpx.MockTransport(handler),
    )
    result = await adapter.create_payment_intent(
        PaymentIntentCommand(
            checkout_id="00000000-0000-0000-0000-000000000002",
            business_reference="diddishop:checkout:checkout-1",
            amount_minor=1500,
            idempotency_key="payment-1",
            payment_method="wave",
            return_url="https://app.diddifree.com/payment/complete",
        )
    )

    body = json.loads(requests[0].content)
    assert requests[0].url.path == "/payfund/v1/payment-intents"
    assert body["amount"] == 1500
    assert body["currency"] == "XOF"
    assert body["payment_method"] == "wave"
    assert body["return_url"] == "https://app.diddifree.com/payment/complete"
    assert "amount_minor" not in body
    assert result["payment_intent_id"] == "00000000-0000-0000-0000-000000000001"


@pytest.mark.anyio
async def test_diddipay_refund_maps_minor_units_to_amount():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={"id": "refund-1"})

    adapter = DiddiPayAdapter(
        base_url="https://pay.test/payfund/v1",
        audience="diddipay",
        transport=httpx.MockTransport(handler),
    )
    result = await adapter.refund(
        "00000000-0000-0000-0000-000000000001",
        500,
        "shop:refund:order-1:1",
    )

    assert requests[0].url.path.endswith("/payment-intents/00000000-0000-0000-0000-000000000001/refunds")
    assert json.loads(requests[0].content) == {"amount": 500, "reason": "diddishop_order"}
    assert requests[0].headers["idempotency-key"] == "shop:refund:order-1:1"
    assert result["refund_id"] == "refund-1"
