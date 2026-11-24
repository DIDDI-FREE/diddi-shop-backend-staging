from app_base.core.errors import InvalidTransitionError
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus
from app_base.shared_kernel.contracts.events import ExternalEvent


DELIVERY_TARGETS = {
    "delivery.created": None,
    "delivery.picked_up": FulfillmentStatus.PICKED_UP,
    "delivery.in_transit": FulfillmentStatus.IN_TRANSIT,
    "delivery.delivered": FulfillmentStatus.DELIVERED,
    "delivery.returned": FulfillmentStatus.RETURNED,
    "delivery.failed": FulfillmentStatus.FAILED,
}


async def handle_diddipay_event(event: ExternalEvent, orders: OrderService) -> None:
    target = {
        "payment.succeeded": (FulfillmentStatus.TO_CONFIRM, "payment.succeeded"),
        "payment.failed": (FulfillmentStatus.CANCELLED, "payment.failed"),
    }.get(event.event_type)
    if target is None:
        return
    await orders.transition(event.aggregate_id, target[0], reason=target[1], actor="diddipay")


async def handle_diddisend_event(event: ExternalEvent, orders: OrderService) -> None:
    target = DELIVERY_TARGETS.get(event.event_type)
    if target is None:
        return
    try:
        await orders.transition(event.aggregate_id, target, reason=event.event_type, actor="diddisend")
    except InvalidTransitionError:
        # The inbox remains the source of duplicate protection; invalid state is an incident.
        raise
