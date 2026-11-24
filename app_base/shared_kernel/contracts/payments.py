from typing import Literal

from pydantic import BaseModel


class PaymentIntentCommand(BaseModel):
    checkout_id: str
    business_reference: str
    amount_minor: int
    currency: Literal["XOF"] = "XOF"
    idempotency_key: str


class PaymentStatus(BaseModel):
    payment_id: str
    business_reference: str
    status: Literal["pending", "succeeded", "failed", "refunded", "partially_refunded"]
    amount_minor: int
    currency: Literal["XOF"]
