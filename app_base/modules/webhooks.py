from fastapi import APIRouter, Request

from app_base.core.webhook_auth import require_webhook_signature
from app_base.shared_kernel.contracts.events import ExternalEvent
from app_base.workers.in_memory_inbox import InMemoryProcessedEvents

router = APIRouter(prefix="/internal/v1/webhooks", tags=["webhooks"])


@router.post("/diddipay")
async def diddipay_webhook(event: ExternalEvent, request: Request):
    await require_webhook_signature(request, request.app.state.settings.diddipay_webhook_secret)
    inbox = request.app.state.processed_events
    if await inbox.seen("diddishop-diddipay", event.event_id):
        return {"status": "duplicate"}
    order_service = request.app.state.order_service
    for order_id in event.payload.get("order_ids", [event.aggregate_id]):
        await order_service.apply_payment_event(order_id, event.event_type, event.payload)
    result_hash = InMemoryProcessedEvents.hash_payload(event.payload)
    await inbox.mark("diddishop-diddipay", event, result_hash)
    return {"status": "processed"}


@router.post("/diddisend")
async def diddisend_webhook(event: ExternalEvent, request: Request):
    await require_webhook_signature(request, request.app.state.settings.diddisend_webhook_secret)
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
