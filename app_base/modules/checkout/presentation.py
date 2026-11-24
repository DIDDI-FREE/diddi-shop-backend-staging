from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    idempotency_key: str
    recipient_name: str | None = None
    recipient_phone: str | None = None
    recipient_email: str | None = None
    dropoff_address: str | None = None
    dropoff_latitude: float | None = None
    dropoff_longitude: float | None = None
