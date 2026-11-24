from app_base.modules.rewards.domain import CampaignSnapshot, RewardReservation


class RewardsService:
    def __init__(self, adapter):
        self.adapter = adapter
        self.reservations: dict[str, RewardReservation] = {}

    async def quote_and_reserve(self, customer_id: str, cart: dict, operation_id: str) -> RewardReservation | None:
        existing = next((r for r in self.reservations.values() if r.operation_id == operation_id), None)
        if existing:
            return existing
        quote = await self.adapter.quote({"customer_id": customer_id, "cart": cart, "operation_id": operation_id})
        if not quote.benefit_id or quote.discount_minor <= 0 or not quote.campaign_id:
            return None
        reserved = await self.adapter.reserve({"customer_id": customer_id, "quote": quote.model_dump(), "operation_id": operation_id})
        snapshot = CampaignSnapshot(quote.campaign_id, 1, quote.benefit_id, quote.discount_minor, quote.currency)
        reservation = RewardReservation(reserved.reservation_id, operation_id, snapshot)
        self.reservations[reservation.reservation_id] = reservation
        return reservation
