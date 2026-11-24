import pytest

from app_base.modules.admin.application import AdminService
from app_base.modules.audit.application import AuditService
from app_base.modules.claims.infra import InMemoryClaimRepository
from app_base.modules.finance import FinanceService
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import Order
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


class Financial:
    async def refund(self, *_): pass
    async def release(self, *_): pass


class Deliveries:
    async def get_by_order(self, _): return None


@pytest.mark.asyncio
async def test_backoffice_reads_through_service_and_records_audit():
    repo = InMemoryOrderRepository()
    await repo.create(Order("o1", "s1", "c1", 1000))
    orders = OrderService(repo, [])
    finance = FinanceService(orders, InMemoryClaimRepository(), Financial())
    audit = AuditService()
    admin = AdminService(orders, InMemoryClaimRepository(), finance, audit, Deliveries())
    result = await admin.read_order("o1", "operator-1")
    assert result["order"].id == "o1"
    assert audit.events[0]["action"] == "admin.read_order"
