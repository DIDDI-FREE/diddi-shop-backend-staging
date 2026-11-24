import pytest

from app_base.modules.delivery.application import DeliveryService
from app_base.modules.delivery.infra import InMemoryDeliveryRepository
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


class Sender:
    async def create_delivery(self, command, payload):
        return {"delivery": {"id": "del-1", "status": "created"}}


@pytest.mark.asyncio
async def test_payment_success_holds_payment_and_moves_order_to_confirmation():
    repo = InMemoryOrderRepository()
    await repo.create(Order("o1", "s1", "c1", 1000))
    service = OrderService(repo, [])
    order = await service.apply_payment_event("o1", "payment.succeeded", {"amount": 1000})
    assert order.payment_status == PaymentStatus.HELD
    assert order.fulfillment_status == FulfillmentStatus.TO_CONFIRM


@pytest.mark.asyncio
async def test_diddisend_event_updates_only_local_projection_and_order():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.READY_FOR_PICKUP)
    await repo.create(order)
    orders = OrderService(repo, [])
    deliveries = InMemoryDeliveryRepository()
    service = DeliveryService(deliveries, Sender(), orders)
    await service.apply_event("o1", "delivery.picked_up", {"delivery_id": "del-1"})
    await service.apply_event("o1", "delivery.in_transit", {"delivery_id": "del-1"})
    delivery = await service.apply_event("o1", "delivery.delivered", {"delivery_id": "del-1", "proof_ref": "proof-1"})
    assert delivery.id == "del-1"
    assert delivery.proof_ref == "proof-1"
    assert (await orders.get("o1")).fulfillment_status == FulfillmentStatus.DELIVERED
