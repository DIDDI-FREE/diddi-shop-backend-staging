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
