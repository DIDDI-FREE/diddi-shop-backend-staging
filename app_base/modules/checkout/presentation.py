from uuid import UUID

from pydantic import BaseModel, Field


class CreateCheckoutRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=255)
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None


class CheckoutQuoteRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None
