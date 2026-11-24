from typing import Literal

from pydantic import BaseModel


class DeliveryQuote(BaseModel):
    amount_minor: int
    currency: str = "XAF"
    expires_at: str | None = None
    provider_reference: str


class DeliveryCommand(BaseModel):
    order_id: str
    origin_service: Literal["diddishop"] = "diddishop"
    prepaid_by_origin: bool = True
    idempotency_key: str


class DeliveryRequest(BaseModel):
    """DiddiSend request shape aligned with DiddiFood's gateway contract."""
    order_reference: str
    idempotency_key: str
    sender_user_id: str
    customer_user_id: str
    recipient_user_id: str | None = None
    recipient_name: str
    recipient_phone: str
    recipient_email: str | None = None
    sender_phone: str | None = None
    sender_email: str | None = None
    pickup_location: dict
    pickup_address: str
    dropoff_location: dict
    dropoff_address: str
    delivery_mode: Literal["door_to_door"] = "door_to_door"
    package: dict
    payment_method: Literal["diddipay"] = "diddipay"
    origin_module: Literal["diddishop"] = "diddishop"
    ready_at: str | None = None
    required_vehicle_type: Literal["motorcycle"] = "motorcycle"
    exclusive: bool = True
    quoted_price: str
    financial_breakdown: dict[str, str | int] | None = None
    prepaid_by_origin: bool = True
