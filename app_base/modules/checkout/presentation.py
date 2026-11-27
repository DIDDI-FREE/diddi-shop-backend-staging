from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app_base.shared_kernel.contracts.payments import PaymentReturnOptions


class CreateCheckoutRequest(PaymentReturnOptions):
    idempotency_key: str = Field(min_length=1, max_length=255)
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None
    payment_method: str = Field(default="wave", pattern=r"^(wave|mtn_momo|orange_money)$")


class RetryCheckoutPaymentRequest(PaymentReturnOptions):
    model_config = ConfigDict(extra="forbid")


class CheckoutQuoteRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    recipient_email: str | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rewards_campaign_id: UUID | None = None
