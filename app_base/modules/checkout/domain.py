from dataclasses import dataclass, field
from enum import StrEnum


class CheckoutStatus(StrEnum):
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"


@dataclass
class Checkout:
    id: str
    customer_id: str
    total_minor: int
    currency: str
    order_ids: list[str] = field(default_factory=list)
    payment_intent_id: str | None = None
    status: CheckoutStatus = CheckoutStatus.PAYMENT_PENDING


class CheckoutRepository:
    async def save(self, checkout: Checkout) -> None:
        raise NotImplementedError

    async def get(self, checkout_id: str) -> Checkout | None:
        raise NotImplementedError
