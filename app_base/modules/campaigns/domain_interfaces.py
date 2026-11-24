from typing import Protocol


class CampaignProjection(Protocol):
    async def get_published_for_checkout(self, customer_id: str, shop_ids: list[str]) -> list[dict]: ...


class CampaignEvents(Protocol):
    async def apply_campaign_event(self, event: dict) -> None: ...
