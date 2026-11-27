import json

import httpx
import pytest
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, use_span

from app_base.core.request_context import RequestContext, set_request_context
from app_base.integrations.auth import ServiceCredential
from app_base.integrations.diddicomms import DiddiCommsAdapter
from app_base.integrations.diddifiles import DiddiFilesAdapter
from app_base.integrations.diddipay import DiddiPayAdapter
from app_base.integrations.diddirewards import DiddiRewardsAdapter
from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.modules.checkout.application.checkout_service import _technical_sender_email
from app_base.integrations.diddisupport import DiddiSupportAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryCommand
from app_base.shared_kernel.contracts.payments import PaymentIntentCommand


def _credential(service: str) -> ServiceCredential:
    return ServiceCredential(service=service, client_id=f"shop-{service}", access_token=f"token-{service}")


def test_diddisend_sender_email_falls_back_to_phone_domain():
    assert _technical_sender_email("+237 690 000 000", "") == "237690000000@diddifree.com"
    assert _technical_sender_email("+237690000000", "sender@example.com") == "sender@example.com"


@pytest.mark.anyio
async def test_diddisend_wire_contract_is_prepaid_and_traceable():
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(201, json={"id": "delivery-1"})

    adapter = DiddiSendAdapter(
        base_url="https://send.test",
        audience="diddisend",
        credential=_credential("diddisend"),
        transport=httpx.MockTransport(handler),
    )
    set_request_context(RequestContext("request-1", "correlation-1"))
    span = NonRecordingSpan(
        SpanContext(0x123, 0x456, is_remote=False, trace_flags=TraceFlags(TraceFlags.SAMPLED))
    )
    with use_span(span):
        await adapter.create_delivery(
            DeliveryCommand(order_id="order-1", idempotency_key="shop:create-delivery:order-1:1"),
            {
                "order_reference": "shop-order:order-1",
                "customer_user_id": "buyer-1",
                "recipient_name": "Buyer",
                "recipient_phone": "237000000000",
                "sender_phone": "+237690000000",
                "sender_email": "shop@diddifree.com",
                "pickup_location": {"lat": 3.8, "lng": 11.5},
                "pickup_address": "pickup",
                "dropoff_location": {"lat": 3.9, "lng": 11.6},
                "dropoff_address": "dropoff",
                "package": {"label": "order-1"},
                "quoted_price": 500,
                "financial_breakdown": {"currency": "XOF", "delivery_fee_minor": 500},
                "origin_payment_reference": "00000000-0000-0000-0000-000000000001",
            },
        )

    request = captured[0]
    body = json.loads(request.content)
    assert request.url.path == "/v1/deliveries"
    assert request.headers["authorization"] == "Bearer token-diddisend"
    assert request.headers["x-client-id"] == "shop-diddisend"
    assert request.headers["x-origin-service"] == "diddishop"
    assert request.headers["idempotency-key"] == "shop:create-delivery:order-1:1"
    assert "traceparent" in request.headers
    assert body["origin_module"] == "diddishop"
    assert body["prepaid_by_origin"] is True
    assert body["payment_method"] == "diddipay"
    assert body["sender_phone"] == "+237690000000"
    assert body["sender_email"] == "shop@diddifree.com"
    assert body["financial_breakdown"]["currency"] == "XOF"
    assert body["origin_payment_reference"] == "00000000-0000-0000-0000-000000000001"


@pytest.mark.anyio
async def test_payment_rewards_files_support_and_comms_routes_are_wired():
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path.endswith("/benefits/quote"):
            return httpx.Response(200, json={"eligible": False, "currency": "XOF"})
        if request.url.path.endswith("/files/upload-session"):
            return httpx.Response(200, json={"id": "file-1"})
        if request.url.path.endswith("/conversation"):
            return httpx.Response(200, json={"id": "conversation-1"})
        return httpx.Response(200, json={"id": "ok"})

    transport = httpx.MockTransport(handler)
    pay = DiddiPayAdapter(base_url="https://pay.test", audience="diddipay", credential=_credential("diddipay"), transport=transport)
    rewards = DiddiRewardsAdapter(base_url="https://rewards.test", audience="diddirewards", credential=_credential("diddirewards"), transport=transport)
    files = DiddiFilesAdapter(base_url="https://files.test", audience="diddifiles", credential=_credential("diddifiles"), transport=transport)
    comms = DiddiCommsAdapter(base_url="https://comms.test", audience="diddicomms", credential=_credential("diddicomms"), transport=transport)
    support = DiddiSupportAdapter(base_url="https://support.test", audience="diddisupport", credential=_credential("diddisupport"), transport=transport)

    await pay.create_payment_intent(PaymentIntentCommand(checkout_id="checkout-1", business_reference="diddishop:checkout:checkout-1", amount_minor=1000, idempotency_key="payment-1", customer_phone="+2250700000000", return_target="app"))
    await rewards.quote({"consumer_id": "buyer-1", "campaign_id": "campaign-1", "amount_initial_minor": 1000, "currency": "XOF"})
    await files.create_upload_session({"purpose": "diddishop_product_image"})
    await comms.open_conversation("diddishop", "order", "00000000-0000-0000-0000-000000000001", "conversation-1")
    await support.get_context("diddishop", "order", "order-1")

    assert [request.url.path for request in captured] == [
        "/payment-intents",
        "/internal/v1/rewards/integrations/diddishop/benefits/quote",
        "/v1/files/upload-session",
        "/comms/v1/tasks/diddishop/order/00000000-0000-0000-0000-000000000001/conversation",
        "/support/v1/internal/context/diddishop/order/order-1",
    ]
    payment_body = json.loads(captured[0].content)
    assert payment_body["amount"] == 1000
    assert payment_body["currency"] == "XOF"
    assert "amount_minor" not in payment_body
    assert "checkout_id" not in payment_body
    assert captured[0].headers["idempotency-key"] == "payment-1"
    assert captured[3].content == b""
    assert captured[3].headers["idempotency-key"] == "conversation-1"
