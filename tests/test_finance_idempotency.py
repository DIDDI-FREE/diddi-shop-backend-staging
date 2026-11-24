from datetime import UTC, datetime

import pytest

from app_base.core.errors import ConflictError
from app_base.modules.claims.domain import ClaimDecision
from app_base.modules.claims.infra import InMemoryClaimRepository
from app_base.modules.finance import FinanceService
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


class Financial:
    def __init__(self):
        self.refunds = []

    async def refund(self, payment_intent_id, amount_minor, idempotency_key):
        self.refunds.append((payment_intent_id, amount_minor, idempotency_key))

    async def release(self, order_id, amount_minor, idempotency_key):
        raise AssertionError("release should not be called in this test")


@pytest.mark.asyncio
async def test_delivery_failure_refund_is_idempotent():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.FAILED)
    order.metadata["payment_intent_id"] = "pi-1"
    await repo.create(order)
    financial = Financial()
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), financial)
    await service.handle_delivery_failure("o1", "delivery.failed")
    await service.handle_delivery_failure("o1", "delivery.failed")
    assert len(financial.refunds) == 1


@pytest.mark.asyncio
async def test_claim_refund_cannot_exceed_order_total():
    repo = InMemoryOrderRepository()
    order = Order("o1", "s1", "c1", 1000, fulfillment_status=FulfillmentStatus.DELIVERED)
    order.metadata["delivered_at"] = datetime.now(UTC)
    await repo.create(order)
    service = FinanceService(OrderService(repo, []), InMemoryClaimRepository(), Financial())
    claim = await service.open_claim("o1", "buyer", "damaged")
    with pytest.raises(ConflictError, match="exceeds"):
        await service.decide(claim.id, ClaimDecision.PARTIAL, 1001)
