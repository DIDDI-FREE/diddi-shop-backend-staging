from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateCheckoutRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=255)
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None
    payment_method: str = Field(default="wave", pattern=r"^(wave|mtn_momo|orange_money)$")
    return_url: str | None = Field(default=None, max_length=2048, pattern=r"^https?://")

    @field_validator("return_url")
    @classmethod
    def validate_return_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        host = (urlparse(value).hostname or "").lower()
        if host != "localhost" and host != "diddifree.com" and not host.endswith(".diddifree.com"):
            raise ValueError("return_url must target diddifree.com or localhost")
        return value


class CheckoutQuoteRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None
