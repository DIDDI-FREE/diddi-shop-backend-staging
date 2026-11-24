from app_base.modules.campaigns.domain import CampaignProjection


class InMemoryCampaignProjection:
    def __init__(self):
        self.items: dict[str, CampaignProjection] = {}

    async def apply(self, campaign: CampaignProjection) -> None:
        current = self.items.get(campaign.campaign_id)
        if current is None or campaign.version >= current.version:
            self.items[campaign.campaign_id] = campaign

    async def published(self) -> list[CampaignProjection]:
        return [c for c in self.items.values() if c.status == "published"]
