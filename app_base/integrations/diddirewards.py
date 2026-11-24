from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.rewards import RewardQuote, RewardReservation


class DiddiRewardsAdapter(ServiceAdapter):
    async def quote(self, payload: dict) -> RewardQuote:
        response = await self.request("POST", "/internal/v1/rewards/benefits/quote", json=payload)
        response.raise_for_status()
        return RewardQuote.model_validate(response.json())

    async def reserve(self, payload: dict) -> RewardReservation:
        response = await self.request("POST", "/internal/v1/rewards/benefits/reservations", json=payload)
        response.raise_for_status()
        return RewardReservation.model_validate(response.json())

    async def consume(self, payload: dict) -> dict:
        response = await self.request("POST", "/internal/v1/rewards/benefits/consumptions", json=payload)
        response.raise_for_status()
        return response.json()

    async def release(self, reservation_id: str, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            f"/internal/v1/rewards/benefits/reservations/{reservation_id}/release",
            headers={"Idempotency-Key": idempotency_key},
        )
        response.raise_for_status()
        return response.json()

    async def correct(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            "/internal/v1/rewards/benefits/corrections",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
