from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignSnapshot:
    campaign_id: str
    campaign_version: int
    benefit_id: str
    discount_minor: int
    currency: str = "XAF"


@dataclass
class RewardReservation:
    reservation_id: str
    operation_id: str
    snapshot: CampaignSnapshot
