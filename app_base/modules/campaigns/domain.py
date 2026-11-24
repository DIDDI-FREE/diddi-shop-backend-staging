from dataclasses import dataclass


@dataclass
class CampaignProjection:
    campaign_id: str
    version: int
    status: str
    name: str
    payload: dict
