import pytest

from app_base.modules.audit.application import AuditService
from app_base.modules.comms.application import CommunicationService
from app_base.modules.rewards.application import RewardsService
from app_base.modules.support.application import SupportContextService
from app_base.shared_kernel.contracts.rewards import RewardQuote, RewardReservation


class RewardsAdapter:
    async def quote(self, payload):
        return RewardQuote(
            eligible=True,
            entitlement_id="ent-1",
            campaign_version_id="version-1",
            discount_minor=100,
            final_amount_minor=900,
            currency="XOF",
        )

    async def reserve(self, payload, idempotency_key):
        return RewardReservation(
            reservation_id="res-1",
            entitlement_id=payload["entitlement_id"],
            operation_id=idempotency_key,
            reserved_amount_minor=100,
        )


class CommsAdapter:
    def __init__(self):
        self.calls = []

    async def open_conversation(self, owner_service, task_type, task_id, idempotency_key):
        self.calls.append((owner_service, task_type, task_id, idempotency_key))
        return {"id": task_id, "state": "open"}


def test_rewards_adapter_has_full_benefit_lifecycle():
    from app_base.integrations.diddirewards import DiddiRewardsAdapter

    assert hasattr(DiddiRewardsAdapter, "quote")
    assert hasattr(DiddiRewardsAdapter, "reserve")
    assert hasattr(DiddiRewardsAdapter, "consume")
    assert hasattr(DiddiRewardsAdapter, "release")
    assert hasattr(DiddiRewardsAdapter, "correct")


@pytest.mark.asyncio
async def test_rewards_adapter_uses_diddishop_contract_routes_and_headers():
    from app_base.integrations.diddirewards import DiddiRewardsAdapter

    class Response:
        def __init__(self, body):
            self.body = body

        def raise_for_status(self):
            return None

        def json(self):
            return self.body

    class Adapter(DiddiRewardsAdapter):
        def __init__(self):
            super().__init__(base_url="https://rewards.example", audience="diddirewards")
            self.calls = []

        async def request(self, method, path, *, headers=None, **kwargs):
            self.calls.append((method, path, headers, kwargs))
            if path.endswith("/quote"):
                return Response({
                    "eligible": True,
                    "entitlement_id": "ent-1",
                    "campaign_version_id": "version-1",
                    "discount_amount_minor": 100,
                    "final_amount_minor": 900,
                    "currency": "XOF",
                    "reason": None,
                })
            if path.endswith("/reserve"):
                return Response({
                    "reservation_id": "res-1",
                    "entitlement_id": "ent-1",
                    "operation_id": "op-1",
                    "reserved_amount_minor": 100,
                    "status": "pending",
                    "duplicate": False,
                })
            return Response({"ok": True})

    adapter = Adapter()
    quote = await adapter.quote({"consumer_id": "u1", "campaign_id": "c1", "amount_initial_minor": 1000, "currency": "XOF"})
    await adapter.reserve({"consumer_id": "u1"}, "op-1")
    await adapter.confirm({"reservation_id": "r1"}, "confirm-1")
    await adapter.release("r1", "release-1")
    await adapter.correct({"consumption_id": "c1", "amount_minor": 100, "reason": "refund"}, "correct-1")

    assert quote.discount_minor == 100
    assert [call[1] for call in adapter.calls] == [
        "/internal/v1/rewards/integrations/diddishop/benefits/quote",
        "/internal/v1/rewards/integrations/diddishop/benefits/reserve",
        "/internal/v1/rewards/integrations/diddishop/benefits/confirm",
        "/internal/v1/rewards/integrations/diddishop/benefits/reservations/r1/release",
        "/internal/v1/rewards/integrations/diddishop/benefits/correct",
    ]
    assert adapter.calls[1][2] == {"Idempotency-Key": "op-1"}
    assert adapter.calls[2][2] == {"Idempotency-Key": "confirm-1"}


@pytest.mark.asyncio
async def test_rewards_reservation_is_idempotent_by_operation():
    service = RewardsService(RewardsAdapter())
    first = await service.quote_and_reserve("u1", "camp-1", 1000, "checkout:1")
    second = await service.quote_and_reserve("u1", "camp-1", 1000, "checkout:1")
    assert first.reservation_id == second.reservation_id
    assert len(service.reservations) == 1


@pytest.mark.asyncio
async def test_comms_opens_a_conversation_without_notification_payload():
    adapter = CommsAdapter()
    service = CommunicationService(adapter)
    await service.open_conversation(
        owner_service="diddishop",
        task_type="order",
        task_id="11111111-1111-1111-1111-111111111111",
        idempotency_key="shop:conversation:order-1:1",
    )
    assert adapter.calls[0] == (
        "diddishop",
        "order",
        "11111111-1111-1111-1111-111111111111",
        "shop:conversation:order-1:1",
    )


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
