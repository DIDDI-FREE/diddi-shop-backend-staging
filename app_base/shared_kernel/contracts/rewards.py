from typing import Literal

from pydantic import BaseModel, Field


class RewardQuote(BaseModel):
    eligible: bool = False
    entitlement_id: str | None = None
    campaign_version_id: str | None = None
    discount_minor: int = Field(default=0, alias="discount_amount_minor")
    final_amount_minor: int = 0
    currency: Literal["XOF"] = "XOF"
    reason: str | None = None

    model_config = {"populate_by_name": True}


class CampaignSnapshot(BaseModel):
    campaign_id: str
    campaign_version_id: str
    entitlement_id: str
    discount_minor: int = Field(ge=0)
    final_amount_minor: int = Field(ge=0)
    currency: Literal["XOF"] = "XOF"


class RewardReservation(BaseModel):
    reservation_id: str
    entitlement_id: str = ""
    operation_id: str
    reserved_amount_minor: int = Field(default=0, ge=0)
    status: str = "pending"
    duplicate: bool = False
    snapshot: CampaignSnapshot | None = None
    consumption_id: str | None = None

    @property
    def discount_minor(self) -> int:
        """Backward-compatible view of the reserved benefit amount."""
        return self.snapshot.discount_minor if self.snapshot else self.reserved_amount_minor
