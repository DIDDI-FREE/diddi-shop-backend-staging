import pytest

from app_base.modules.audit.application import AuditService
from app_base.modules.comms.application import CommunicationService
from app_base.modules.rewards.application import RewardsService
from app_base.modules.support.application import SupportContextService
from app_base.shared_kernel.contracts.rewards import RewardQuote, RewardReservation


class RewardsAdapter:
    async def quote(self, payload):
        return RewardQuote(campaign_id="camp-1", benefit_id="benefit-1", discount_minor=100, operation_id=payload["operation_id"])

    async def reserve(self, payload):
        return RewardReservation(reservation_id="res-1", operation_id=payload["operation_id"], discount_minor=100)


class CommsAdapter:
    def __init__(self):
        self.calls = []

    async def create_task(self, payload, idempotency_key):
        self.calls.append((payload, idempotency_key))
        return {"task_id": "task-1"}


def test_rewards_adapter_has_full_benefit_lifecycle():
    from app_base.integrations.diddirewards import DiddiRewardsAdapter

    assert hasattr(DiddiRewardsAdapter, "quote")
    assert hasattr(DiddiRewardsAdapter, "reserve")
    assert hasattr(DiddiRewardsAdapter, "consume")
    assert hasattr(DiddiRewardsAdapter, "release")
    assert hasattr(DiddiRewardsAdapter, "correct")


@pytest.mark.asyncio
async def test_rewards_reservation_is_idempotent_by_operation():
    service = RewardsService(RewardsAdapter())
    first = await service.quote_and_reserve("u1", {"total": 1000}, "checkout:1")
    second = await service.quote_and_reserve("u1", {"total": 1000}, "checkout:1")
    assert first.reservation_id == second.reservation_id
    assert len(service.reservations) == 1


@pytest.mark.asyncio
async def test_comms_uses_event_id_as_idempotency_key():
    adapter = CommsAdapter()
    service = CommunicationService(adapter)
    await service.enqueue({"event_id": "evt-1", "event_type": "order.created", "payload": {"customer_id": "u1"}})
    assert adapter.calls[0][1] == "shop:notify:evt-1:1"


@pytest.mark.asyncio
async def test_support_context_declares_external_sources():
    class Orders:
        async def get(self, _):
            return {"id": "o1"}
    class Deliveries:
        async def get_by_order(self, _):
            return {"id": "d1"}
    class Claims:
        async def get_open_for_order(self, _):
            return None
    context = await SupportContextService(Orders(), Deliveries(), Claims()).build_order_context("o1")
    assert context["source_of_truth"]["delivery"] == "diddisend"


@pytest.mark.asyncio
async def test_audit_keeps_actor_and_resource():
    service = AuditService()
    await service.append("claim.decide", "agent-1", "claim-1", {"decision": "buyer"})
    assert service.events[0]["actor"] == "agent-1"
    assert service.events[0]["resource"] == "claim-1"
