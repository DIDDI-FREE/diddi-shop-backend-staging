from datetime import UTC, datetime

import pytest

from app_base.modules.catalog.domain import Product, ProductStatus
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.claims.domain import ClaimDecision
from app_base.modules.claims.infra import InMemoryClaimRepository
from app_base.modules.finance import FinanceService
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


class Financial:
    def __init__(self):
        self.refunds = []
        self.releases = []

    async def refund(self, payment_intent_id, amount_minor, idempotency_key):
        self.refunds.append((payment_intent_id, amount_minor, idempotency_key))

    async def release(self, order_id, amount_minor, idempotency_key):
        self.releases.append((order_id, amount_minor, idempotency_key))


class Delivery:
    def __init__(self):
        self.cancelled = []

    async def cancel_delivery(self, delivery_id, idempotency_key):
        self.cancelled.append((delivery_id, idempotency_key))


@pytest.mark.asyncio
async def test_claim_blocks_release_and_buyer_decision_requests_refund():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.DELIVERED, payment_status=PaymentStatus.HELD)
    order.metadata["delivered_at"] = datetime.now(UTC)
    await repo.create(order)
    financial = Financial()
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), financial)
    claim = await service.open_claim("o1", "buyer-1", "damaged")
    assert (await repo.get("o1")).fulfillment_status == FulfillmentStatus.DISPUTED
    await service.decide(claim.id, ClaimDecision.BUYER, 1000)
    assert financial.refunds[0][1] == 1000
    assert (await repo.get("o1")).payment_status == PaymentStatus.REFUND_PENDING


@pytest.mark.asyncio
async def test_seller_release_is_requested_only_after_eligibility():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.DELIVERED)
    order.metadata["release_eligible_at"] = datetime(2020, 1, 1, tzinfo=UTC)
    await repo.create(order)
    financial = Financial()
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), financial, seller_release_enabled=True)
    await service.release_if_eligible("o1", datetime.now(UTC))
    assert financial.releases[0][0] == "o1"
    assert (await repo.get("o1")).payment_status == PaymentStatus.RELEASE_PENDING


@pytest.mark.asyncio
async def test_mvp_does_not_release_seller_funds():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.DELIVERED, payment_status=PaymentStatus.HELD)
    order.metadata["release_eligible_at"] = datetime(2020, 1, 1, tzinfo=UTC)
    await repo.create(order)
    financial = Financial()
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), financial)

    await service.release_if_eligible("o1", datetime.now(UTC))

    assert financial.releases == []
    assert (await repo.get("o1")).payment_status == PaymentStatus.HELD


@pytest.mark.asyncio
async def test_cancel_restores_stock_and_cancels_delivery_before_refund():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.TO_CONFIRM)
    order.delivery_id = "del-1"
    order.metadata["lines"] = [{"product_id": "p1", "quantity": 1}]
    await repo.create(order)
    products = InMemoryProductRepository()
    await products.save(Product("p1", "s1", "Item", "", 1000, "XOF", 0, "x", [], ProductStatus.PUBLISHED))
    financial = Financial()
    delivery = Delivery()
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), financial, products, delivery)
    await service.cancel("o1", "buyer_requested")
    assert products.items["p1"].stock == 1
    assert delivery.cancelled[0][0] == "del-1"
    assert financial.refunds[0][1] == 1000
