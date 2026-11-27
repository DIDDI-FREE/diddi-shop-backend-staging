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
    service = DeliveryService(
        deliveries,
        Sender(),
        orders,
        diddisend_sender_phone="+237690000000",
        diddisend_sender_email="sender@diddifree.com",
    )
    await service.apply_event("o1", "delivery.picked_up", {"delivery_id": "del-1"})
    await service.apply_event("o1", "delivery.in_transit", {"delivery_id": "del-1"})
    delivery = await service.apply_event(
        "o1",
        "delivery.delivered",
        {
            "delivery_id": "del-1",
            "proof_ref": "proof-1",
            "courier": {"courier_id": "courier-1", "display_name": "Courier"},
            "position": {"lat": 3.8, "lng": 11.5, "recorded_at": "2026-11-26T10:00:00Z"},
        },
    )
    assert delivery.id == "del-1"
    assert delivery.proof_ref == "proof-1"
    assert delivery.courier["id"] == "courier-1"
    assert delivery.position["latitude"] == 3.8
    assert (await orders.get("o1")).fulfillment_status == FulfillmentStatus.DELIVERED


@pytest.mark.asyncio
async def test_seller_ready_immediately_requests_diddisend_and_is_retryable():
    class CountingSender:
        def __init__(self):
            self.calls = 0
            self.payloads = []

        async def create_delivery(self, command, payload):
            self.calls += 1
            self.payloads.append(payload)
            return {"delivery": {"id": "del-ready-1", "status": "created"}}

    repo = InMemoryOrderRepository()
    order = Order(
        "o-ready",
        "s1",
        "c1",
        1000,
        fulfillment_status=FulfillmentStatus.TO_PREPARE,
        metadata={"payment_intent_id": "00000000-0000-0000-0000-000000000001"},
    )
    await repo.create(order)
    orders = OrderService(repo, [])
    deliveries = InMemoryDeliveryRepository()
    sender = CountingSender()
    service = DeliveryService(
        deliveries,
        sender,
        orders,
        diddisend_sender_phone="+237690000000",
    )

    first = await service.mark_ready_and_request("o-ready")
    second = await service.mark_ready_and_request("o-ready")

    assert first.id == second.id == "del-ready-1"
    assert sender.calls == 1
    assert sender.payloads[0]["sender_phone"] == "+237690000000"
    assert sender.payloads[0]["sender_email"] == "237690000000@diddifree.com"
    assert sender.payloads[0]["origin_payment_reference"] == "00000000-0000-0000-0000-000000000001"
    assert sender.payloads[0]["order_reference"] == "diddishop:checkout:c1"
    saved = await orders.get("o-ready")
    assert saved.fulfillment_status == FulfillmentStatus.READY_FOR_PICKUP
    assert saved.delivery_id == "del-ready-1"
