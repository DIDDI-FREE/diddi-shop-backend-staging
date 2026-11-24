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
