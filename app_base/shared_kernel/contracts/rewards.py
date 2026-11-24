from pydantic import BaseModel


class RewardQuote(BaseModel):
    campaign_id: str | None = None
    benefit_id: str | None = None
    discount_minor: int = 0
    currency: str = "XAF"
    operation_id: str


class RewardReservation(BaseModel):
    reservation_id: str
    operation_id: str
    discount_minor: int
