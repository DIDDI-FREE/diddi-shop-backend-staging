from fastapi import APIRouter, Request

from app_base.shared_kernel.contracts.events import ExternalEvent
from app_base.workers.in_memory_inbox import InMemoryProcessedEvents

router = APIRouter(prefix="/internal/v1/webhooks", tags=["webhooks"])


@router.post("/diddipay")
async def diddipay_webhook(event: ExternalEvent, request: Request):
    inbox: InMemoryProcessedEvents = request.app.state.processed_events
    if await inbox.seen("diddishop-diddipay", event.event_id):
        return {"status": "duplicate"}
    order_service = request.app.state.order_service
    for order_id in event.payload.get("order_ids", [event.aggregate_id]):
        await order_service.apply_payment_event(order_id, event.event_type, event.payload)
    await inbox.mark("diddishop-diddipay", event, inbox.hash_payload(event.payload))
    return {"status": "processed"}


@router.post("/diddisend")
async def diddisend_webhook(event: ExternalEvent, request: Request):
    inbox: InMemoryProcessedEvents = request.app.state.processed_events
    if await inbox.seen("diddishop-diddisend", event.event_id):
        return {"status": "duplicate"}
    delivery_service = request.app.state.delivery_service
    await delivery_service.apply_event(event.aggregate_id, event.event_type, event.payload)
    await inbox.mark("diddishop-diddisend", event, inbox.hash_payload(event.payload))
    return {"status": "processed"}
