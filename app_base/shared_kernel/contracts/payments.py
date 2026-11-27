import re
from typing import Literal, TypeGuard

from pydantic import BaseModel, Field

from app_base.core.errors import PaymentPhoneRequiredError

CUSTOMER_PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"


def valid_customer_phone(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and re.fullmatch(CUSTOMER_PHONE_PATTERN, value) is not None


def require_customer_phone(value: object) -> str:
    if not valid_customer_phone(value):
        raise PaymentPhoneRequiredError("A valid E.164 recipient_phone is required for payment")
    return value


class PaymentIntentCommand(BaseModel):
    checkout_id: str
    business_reference: str
    amount_minor: int
    currency: Literal["XOF"] = "XOF"
    idempotency_key: str
    payment_method: Literal["wave", "mtn_momo", "orange_money"] = "wave"
    return_url: str | None = None
    customer_phone: str = Field(pattern=CUSTOMER_PHONE_PATTERN)


class PaymentStatus(BaseModel):
    payment_id: str
    business_reference: str
    status: Literal["pending", "succeeded", "failed", "refunded", "partially_refunded"]
    amount_minor: int
    currency: Literal["XOF"]
