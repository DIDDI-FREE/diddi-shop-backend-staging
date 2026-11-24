from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.rewards import RewardQuote, RewardReservation


class DiddiRewardsAdapter(ServiceAdapter):
    _shop_prefix = "/internal/v1/rewards/integrations/diddishop"

    async def quote(self, payload: dict) -> RewardQuote:
        response = await self.request("POST", f"{self._shop_prefix}/benefits/quote", json=payload)
        response.raise_for_status()
        return RewardQuote.model_validate(response.json())

    async def reserve(self, payload: dict, idempotency_key: str) -> RewardReservation:
        response = await self.request(
            "POST",
            f"{self._shop_prefix}/benefits/reserve",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return RewardReservation.model_validate(response.json())

    async def confirm(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            f"{self._shop_prefix}/benefits/confirm",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def consume(self, payload: dict, idempotency_key: str) -> dict:
        """Compatibility alias for the Rewards 'confirm' operation."""
        return await self.confirm(payload, idempotency_key)

    async def release(self, reservation_id: str, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            f"{self._shop_prefix}/benefits/reservations/{reservation_id}/release",
            headers={"Idempotency-Key": idempotency_key},
        )
        response.raise_for_status()
        return response.json()

    async def correct(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            f"{self._shop_prefix}/benefits/correct",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
