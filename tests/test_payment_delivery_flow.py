import pytest

from app_base.modules.delivery.application import DeliveryService
from app_base.modules.delivery.infra import InMemoryDeliveryRepository
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository
from app_base.modules.rewards.application import RewardsService
from app_base.shared_kernel.contracts.rewards import CampaignSnapshot, RewardReservation


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
async def test_payment_events_confirm_and_correct_rewards_using_persisted_snapshot():
    class RewardsAdapter:
        def __init__(self):
            self.confirm_calls = []
            self.correct_calls = []

        async def confirm(self, payload, idempotency_key):
            self.confirm_calls.append((payload, idempotency_key))
            return {"consumption_id": "cons-1"}

        async def correct(self, payload, idempotency_key):
            self.correct_calls.append((payload, idempotency_key))
            return {"correction_id": "corr-1"}

    adapter = RewardsAdapter()
    rewards = RewardsService(adapter)
    reservation = RewardReservation(
        reservation_id="res-1",
        entitlement_id="ent-1",
        operation_id="diddishop:benefit-reservation:o1:1",
        reserved_amount_minor=100,
        snapshot=CampaignSnapshot(
            campaign_id="camp-1",
            campaign_version_id="version-1",
            entitlement_id="ent-1",
            discount_minor=100,
            final_amount_minor=900,
        ),
    )
    order = Order("o1", "s1", "c1", 900, metadata={"rewards": rewards.to_metadata(reservation)})
    repo = InMemoryOrderRepository()
    await repo.create(order)
    service = OrderService(repo, [], rewards)

    await service.apply_payment_event("o1", "payment.succeeded", {"amount_minor": 900, "payment_intent_id": "pi-1"})
    assert adapter.confirm_calls[0][0]["applied_discount_minor"] == 100
    assert (await repo.get("o1")).metadata["rewards"]["consumption_id"] == "cons-1"

    await service.apply_payment_event("o1", "payment.refunded", {"amount_minor": 100, "refund_id": "refund-1"})
    assert adapter.correct_calls[0][0]["consumption_id"] == "cons-1"


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
