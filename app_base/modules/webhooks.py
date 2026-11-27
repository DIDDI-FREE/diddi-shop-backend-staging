from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app_base.core.api_contracts import WebhookResponse
from app_base.core.webhook_auth import require_webhook_signature
from app_base.shared_kernel.contracts.events import (
    DiddiPayCallbackEnvelope,
    DiddiSendCallbackEnvelope,
    ExternalEvent,
)
from app_base.workers.in_memory_inbox import InMemoryProcessedEvents

router = APIRouter(prefix="/internal/v1/webhooks", tags=["webhooks"])


def _checkout_id_from_business_reference(reference: Any) -> str | None:
    if not isinstance(reference, str):
        return None
    prefix = "diddishop:checkout:"
    if not reference.startswith(prefix):
        return None
    checkout_id = reference.removeprefix(prefix).strip()
    return checkout_id or None


def _order_id_from_reference(reference: Any) -> str | None:
    if not isinstance(reference, str):
        return None
    prefix = "shop-order:"
    if not reference.startswith(prefix):
        return None
    order_id = reference.removeprefix(prefix).strip()
    return order_id or None


def _normalize_diddipay_event(raw: object) -> tuple[ExternalEvent, bool]:
    """Adapt DiddiPay's signed envelope to the internal event shape.

    The boolean indicates whether the event is the native DiddiPay envelope.
    Native callbacks must identify a checkout/order explicitly; legacy
    DiddiShop envelopes may still use ``aggregate_id`` as their fallback.
    """
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="DiddiPay callback must be a JSON object")

    if {"id", "type", "occurred_at", "data"}.issubset(raw):
        envelope = DiddiPayCallbackEnvelope.model_validate(raw)
        payload = dict(envelope.data)
        checkout_id = payload.get("checkout_id") or _checkout_id_from_business_reference(
            payload.get("business_reference")
        )
        if checkout_id:
            payload["checkout_id"] = checkout_id
        aggregate_id = payload.get("order_id") or checkout_id or envelope.id
        return (
            ExternalEvent(
                event_id=envelope.id,
                event_type=envelope.type,
                aggregate_id=aggregate_id,
                payload=payload,
            ),
            True,
        )

    return ExternalEvent.model_validate(raw), False


def _normalize_diddisend_event(raw: object) -> tuple[ExternalEvent, bool]:
    """Adapt DiddiSend's signed delivery envelope to the internal shape."""
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="DiddiSend callback must be a JSON object")

    if {"event_id", "event_type", "delivery_id", "occurred_at", "data"}.issubset(raw):
        envelope = DiddiSendCallbackEnvelope.model_validate(raw)
        payload = dict(envelope.data)
        payload.setdefault("delivery_id", envelope.delivery_id)
        payload.setdefault("order_reference", envelope.order_reference)
        payload.setdefault("status", envelope.status)
        payload.setdefault("origin_module", envelope.origin_module)
        payload.setdefault("currency", envelope.currency)
        if envelope.financial_breakdown is not None:
            payload.setdefault("financial_breakdown", envelope.financial_breakdown)
        order_id = payload.get("order_id") or _order_id_from_reference(envelope.order_reference)
        if order_id:
            payload["order_id"] = order_id
        return (
            ExternalEvent(
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                aggregate_id=order_id or envelope.delivery_id,
                payload=payload,
            ),
            True,
        )

    return ExternalEvent.model_validate(raw), False


@router.post("/diddipay", response_model=WebhookResponse)
async def diddipay_webhook(request: Request):
    await require_webhook_signature(
        request,
        request.app.state.settings.diddipay_webhook_secret,
        header_name="X-DiddiPay-Signature",
        timestamp_header=None,
    )
    try:
        raw = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="DiddiPay callback must be valid JSON") from exc
    event, is_diddipay_envelope = _normalize_diddipay_event(raw)
    inbox = request.app.state.processed_events
    if await inbox.seen("diddishop-diddipay", event.event_id):
        return {"status": "duplicate"}
    order_service = request.app.state.order_service
    checkout_ids = set()
    order_ids = event.payload.get("order_ids")
    if isinstance(order_ids, str):
        order_ids = [order_ids]
    if not order_ids and event.payload.get("checkout_id"):
        checkout = await request.app.state.checkout_service.get(event.payload["checkout_id"])
        order_ids = checkout.order_ids
    if not order_ids and is_diddipay_envelope and not event.payload.get("order_id"):
        raise HTTPException(
            status_code=422,
            detail="DiddiPay callback is not linked to a DiddiShop checkout or order",
        )
    for order_id in order_ids or [event.aggregate_id]:
        order = await order_service.apply_payment_event(order_id, event.event_type, event.payload)
        checkout_ids.add(order.checkout_id)
    if event.payload.get("checkout_id"):
        checkout_ids.add(event.payload["checkout_id"])
    for checkout_id in checkout_ids:
        await request.app.state.checkout_service.apply_payment_event(checkout_id, event.event_type, event.payload)
    result_hash = InMemoryProcessedEvents.hash_payload(event.payload)
    await inbox.mark("diddishop-diddipay", event, result_hash)
    return {"status": "processed"}


@router.post("/diddisend", response_model=WebhookResponse)
async def diddisend_webhook(request: Request):
    await require_webhook_signature(
        request,
        request.app.state.settings.diddisend_webhook_secret,
        header_name="X-DiddiSend-Signature",
        timestamp_header=None,
    )
    try:
        raw = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="DiddiSend callback must be valid JSON") from exc
    event, is_diddisend_envelope = _normalize_diddisend_event(raw)
    # Coverage verification uses the PaymentIntent business_reference as the
    # DiddiSend order_reference. Resolve that checkout reference back to the
    # single Shop order before applying the delivery event. A multi-order
    # checkout is intentionally rejected here because one prepaid PaymentIntent
    # cannot identify a unique delivery order under the current contract.
    if is_diddisend_envelope and not event.payload.get("order_id"):
        checkout_id = _checkout_id_from_business_reference(event.payload.get("order_reference"))
        if checkout_id:
            checkout = await request.app.state.checkout_service.get(checkout_id)
            if len(checkout.order_ids) == 1:
                event = event.model_copy(
                    update={
                        "aggregate_id": checkout.order_ids[0],
                        "payload": {**event.payload, "order_id": checkout.order_ids[0]},
                    }
                )
    if is_diddisend_envelope and not event.payload.get("order_id"):
        raise HTTPException(
            status_code=422,
            detail="DiddiSend callback is not linked to a DiddiShop order",
        )
    inbox = request.app.state.processed_events
    if await inbox.seen("diddishop-diddisend", event.event_id):
        return {"status": "duplicate"}
    delivery_service = request.app.state.delivery_service
    await delivery_service.apply_event(event.aggregate_id, event.event_type, event.payload)
    if event.event_type in {"delivery.failed", "delivery.returned"}:
        await request.app.state.finance_service.handle_delivery_failure(event.aggregate_id, event.event_type)
    result_hash = InMemoryProcessedEvents.hash_payload(event.payload)
    await inbox.mark("diddishop-diddisend", event, result_hash)
    return {"status": "processed"}
