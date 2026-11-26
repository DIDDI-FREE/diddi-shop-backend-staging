import hashlib
import hmac
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app_base.core.webhook_auth import require_webhook_signature
from app_base.modules.webhooks import _normalize_diddipay_event, _normalize_diddisend_event


def test_diddipay_envelope_is_normalized_from_business_reference():
    event, is_native = _normalize_diddipay_event(
        {
            "id": "pay-event-1",
            "type": "payment.succeeded",
            "occurred_at": "2026-11-26T12:00:00Z",
            "data": {
                "payment_intent_id": "pi-1",
                "business_reference": "diddishop:checkout:checkout-1",
                "amount": "1250",
                "currency": "XOF",
            },
        }
    )

    assert is_native is True
    assert event.event_id == "pay-event-1"
    assert event.event_type == "payment.succeeded"
    assert event.aggregate_id == "checkout-1"
    assert event.payload["checkout_id"] == "checkout-1"


def test_legacy_external_event_remains_supported():
    event, is_native = _normalize_diddipay_event(
        {
            "event_id": "legacy-1",
            "event_type": "payment.failed",
            "aggregate_id": "order-1",
            "payload": {"order_ids": ["order-1"]},
        }
    )

    assert is_native is False
    assert event.event_id == "legacy-1"
    assert event.aggregate_id == "order-1"


def test_diddisend_envelope_resolves_order_from_order_reference():
    event, is_native = _normalize_diddisend_event(
        {
            "event_id": "delivery-event-1",
            "event_version": "1",
            "event_type": "delivery.in_transit",
            "source_service": "diddisend",
            "delivery_id": "delivery-1",
            "order_reference": "shop-order:order-1",
            "status": "in_transit",
            "origin_module": "diddishop",
            "currency": "XOF",
            "financial_breakdown": None,
            "occurred_at": "2026-11-26T12:00:00Z",
            "data": {"courier": {"id": "courier-1"}},
        }
    )

    assert is_native is True
    assert event.event_id == "delivery-event-1"
    assert event.aggregate_id == "order-1"
    assert event.payload["delivery_id"] == "delivery-1"
    assert event.payload["order_id"] == "order-1"


@pytest.mark.asyncio
async def test_diddipay_signature_uses_raw_body_and_provider_header_without_timestamp():
    secret = "shared-diddipay-secret"
    body = b'{"data":{"currency":"XOF"},"id":"event-1","type":"payment.succeeded"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    app = SimpleNamespace(state=SimpleNamespace(settings=SimpleNamespace(environment="staging")))

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/internal/v1/webhooks/diddipay",
            "headers": [
                (b"x-diddipay-signature", signature.encode()),
                (b"x-webhook-timestamp", b"must-not-be-signed"),
            ],
            "app": app,
        },
        receive,
    )

    await require_webhook_signature(
        request,
        secret,
        header_name="X-DiddiPay-Signature",
        timestamp_header=None,
    )


@pytest.mark.asyncio
async def test_diddisend_signature_accepts_sha256_prefix_without_timestamp():
    secret = "shared-diddisend-secret"
    body = b'{"data":{"order_id":"order-1"},"event_id":"event-1"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    app = SimpleNamespace(state=SimpleNamespace(settings=SimpleNamespace(environment="staging")))

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/internal/v1/webhooks/diddisend",
            "headers": [(b"x-diddisend-signature", f"sha256={digest}".encode())],
            "app": app,
        },
        receive,
    )

    await require_webhook_signature(
        request,
        secret,
        header_name="X-DiddiSend-Signature",
        timestamp_header=None,
    )
