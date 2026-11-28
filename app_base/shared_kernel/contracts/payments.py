import re
from typing import Literal, TypeGuard
from urllib.parse import unquote, urlsplit

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app_base.core.errors import (
    PaymentPhoneRequiredError,
    PaymentReturnInvalidError,
    PaymentReturnRequiredError,
)
from app_base.shared_kernel.money import XofAmount

CUSTOMER_PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"
DEFAULT_PAYMENT_RETURN_URL = "https://diddishop-backend.diddifree.com/payments/return"


def valid_customer_phone(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and re.fullmatch(CUSTOMER_PHONE_PATTERN, value) is not None


def require_customer_phone(value: object) -> str:
    if not valid_customer_phone(value):
        raise PaymentPhoneRequiredError("A valid E.164 recipient_phone is required for payment")
    return value


class PaymentReturnOptions(BaseModel):
    return_url: str | None = Field(default=None, min_length=1, max_length=2048)
    return_target: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("return_url")
    @classmethod
    def validate_return_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        decoded = unquote(value)
        parts = urlsplit(value)
        host = (parts.hostname or "").lower()
        if (
            parts.scheme != "https"
            or (host != "diddifree.com" and not host.endswith(".diddifree.com"))
            or parts.username is not None or parts.password is not None
            or parts.port not in (None, 443)
            or "\\" in decoded or any(ord(char) <= 32 or ord(char) == 127 for char in decoded)
            or ".." in unquote(parts.path).split("/")
            or parts.fragment
        ):
            raise ValueError("return_url must be an HTTPS DiddiFree URL without credentials, fragment or traversal")
        return value

    @model_validator(mode="after")
    def exclusive_return(self):
        if self.return_url is not None and self.return_target is not None:
            raise ValueError("use return_url or return_target, never both")
        return self


def require_payment_return(return_url: str | None, return_target: str | None) -> PaymentReturnOptions:
    try:
        options = PaymentReturnOptions(return_url=return_url, return_target=return_target)
    except ValidationError as exc:
        raise PaymentReturnInvalidError("Invalid payment return destination") from exc
    if not options.return_url and not options.return_target:
        raise PaymentReturnRequiredError("A payment return destination must be configured")
    return options


class PaymentIntentCommand(PaymentReturnOptions):
    checkout_id: str
    business_reference: str
    amount_minor: XofAmount
    currency: Literal["XOF"] = "XOF"
    idempotency_key: str
    payment_method: Literal["wave", "mtn_momo", "orange_money"] = "wave"
    customer_phone: str = Field(pattern=CUSTOMER_PHONE_PATTERN)


class PaymentStatus(BaseModel):
    payment_id: str
    business_reference: str
    status: Literal["pending", "succeeded", "failed", "refunded", "partially_refunded"]
    amount_minor: XofAmount
    currency: Literal["XOF"]
