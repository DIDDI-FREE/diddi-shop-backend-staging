from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from app_base.shared_kernel.currency import require_xof


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
    payment: dict | None = None
    subtotal_minor: int = 0
    delivery_fee_minor: int = 0
    discount_minor: int = 0
    shop_breakdowns: list[dict] = field(default_factory=list)
    payment_attempt: int = 1
    payment_idempotency_key: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        require_xof(self.currency)
        self.status = CheckoutStatus(self.status)


class CheckoutRepository:
    async def save(self, checkout: Checkout) -> None:
        raise NotImplementedError

    async def get(self, checkout_id: str) -> Checkout | None:
        raise NotImplementedError

    async def list_for_customer(self, customer_id: str) -> list[Checkout]:
        raise NotImplementedError
