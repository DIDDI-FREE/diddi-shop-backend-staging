from datetime import UTC, datetime, timedelta

from app_base.modules.rewards.domain import CampaignSnapshot, RewardReservation


class RewardsService:
    def __init__(self, adapter):
        self.adapter = adapter
        self.reservations: dict[str, RewardReservation] = {}

    async def quote_and_reserve(
        self,
        customer_id: str,
        campaign_id: str,
        amount_initial_minor: int,
        operation_id: str,
        *,
        expires_at: datetime | None = None,
    ) -> RewardReservation | None:
        if amount_initial_minor <= 0:
            return None
        existing = next((r for r in self.reservations.values() if r.operation_id == operation_id), None)
        if existing:
            return existing
        quote = await self.adapter.quote({
            "consumer_id": customer_id,
            "campaign_id": campaign_id,
            "amount_initial_minor": amount_initial_minor,
            "currency": "XOF",
        })
        if not quote.eligible or not quote.entitlement_id or not quote.campaign_version_id or quote.discount_minor <= 0:
            return None
        expiry = expires_at or datetime.now(UTC) + timedelta(minutes=30)
        reserved = await self.adapter.reserve(
            {
                "consumer_id": customer_id,
                "entitlement_id": quote.entitlement_id,
                "service_operation_id": operation_id,
                "requested_amount_minor": quote.discount_minor,
                "expires_at": expiry.isoformat(),
            },
            operation_id,
        )
        snapshot = CampaignSnapshot(
            campaign_id=campaign_id,
            campaign_version_id=quote.campaign_version_id,
            entitlement_id=quote.entitlement_id,
            discount_minor=quote.discount_minor,
            final_amount_minor=quote.final_amount_minor,
            currency="XOF",
        )
        reserved.snapshot = snapshot
        self.reservations[reserved.reservation_id] = reserved
        return reserved

    @staticmethod
    def from_metadata(payload: dict) -> RewardReservation:
        """Rehydrate a reservation after a process restart or event retry."""
        return RewardReservation.model_validate(payload)

    @staticmethod
    def to_metadata(reservation: RewardReservation) -> dict:
        return reservation.model_dump(mode="json")

    async def consume(
        self,
        reservation: RewardReservation,
        order_id: str,
        *,
        client_paid_minor: int,
        professional_payout_minor: int,
        diddi_contribution_minor: int,
        payment_reference: str | None = None,
    ) -> dict:
        result = await self.adapter.confirm({
            "reservation_id": reservation.reservation_id,
            "service_operation_id": order_id,
            "applied_discount_minor": reservation.discount_minor,
            "client_paid_minor": client_paid_minor,
            "professional_payout_minor": professional_payout_minor,
            "diddi_contribution_minor": diddi_contribution_minor,
            "payment_reference": payment_reference,
        }, f"diddishop:benefit-confirmation:{order_id}:1")
        reservation.consumption_id = result.get("consumption_id")
        return result

    async def release(self, reservation: RewardReservation) -> dict:
        return await self.adapter.release(
            reservation.reservation_id,
            f"diddishop:benefit-release:{reservation.reservation_id}:1",
        )

    async def correct(
        self,
        reservation: RewardReservation,
        reason: str,
        amount_minor: int,
        payment_reference: str | None = None,
        operation_id: str | None = None,
    ) -> dict:
        if not reservation.consumption_id:
            raise ValueError("Rewards correction requires a confirmed consumption")
        return await self.adapter.correct(
            {
                "consumption_id": reservation.consumption_id,
                "amount_minor": amount_minor,
                "reason": reason,
                "payment_reference": payment_reference,
            },
            f"diddishop:benefit-correction:{reservation.consumption_id}:{operation_id or '1'}",
        )
