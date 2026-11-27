from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from app_base.core.errors import InvalidTransitionError
from app_base.shared_kernel.currency import require_xof


class FulfillmentStatus(StrEnum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    TO_CONFIRM = "TO_CONFIRM"
    TO_PREPARE = "TO_PREPARE"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    DISPUTED = "DISPUTED"
    CLOSED = "CLOSED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    HELD = "HELD"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"
    RELEASE_BLOCKED = "RELEASE_BLOCKED"
    RELEASE_PENDING = "RELEASE_PENDING"
    RELEASED = "RELEASED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


ALLOWED_TRANSITIONS: dict[FulfillmentStatus, set[FulfillmentStatus]] = {
    FulfillmentStatus.PAYMENT_PENDING: {FulfillmentStatus.TO_CONFIRM, FulfillmentStatus.CANCELLED},
    FulfillmentStatus.TO_CONFIRM: {FulfillmentStatus.TO_PREPARE, FulfillmentStatus.CANCELLED},
    FulfillmentStatus.TO_PREPARE: {FulfillmentStatus.READY_FOR_PICKUP, FulfillmentStatus.CANCELLED},
    FulfillmentStatus.READY_FOR_PICKUP: {FulfillmentStatus.PICKED_UP, FulfillmentStatus.RETURNED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED},
    FulfillmentStatus.PICKED_UP: {FulfillmentStatus.IN_TRANSIT, FulfillmentStatus.DELIVERED, FulfillmentStatus.RETURNED, FulfillmentStatus.FAILED},
    FulfillmentStatus.IN_TRANSIT: {FulfillmentStatus.DELIVERED, FulfillmentStatus.RETURNED, FulfillmentStatus.FAILED},
    FulfillmentStatus.DELIVERED: {FulfillmentStatus.DISPUTED, FulfillmentStatus.CLOSED},
    FulfillmentStatus.DISPUTED: {FulfillmentStatus.CLOSED},
    FulfillmentStatus.RETURNED: {FulfillmentStatus.CLOSED},
    FulfillmentStatus.FAILED: {FulfillmentStatus.CLOSED},
    FulfillmentStatus.CANCELLED: set(),
    FulfillmentStatus.CLOSED: set(),
}


@dataclass
class Order:
    id: str
    shop_id: str
    checkout_id: str
    total_minor: int
    currency: str = "XOF"
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.PAYMENT_PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    delivery_id: str | None = None
    version: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    seller_confirmation_deadline: str | None = None
    status_history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        require_xof(self.currency)
        # JSON stores strings; every loaded aggregate must recover domain enums.
        self.fulfillment_status = FulfillmentStatus(self.fulfillment_status)
        self.payment_status = PaymentStatus(self.payment_status)
        if self.seller_confirmation_deadline is None:
            try:
                created = datetime.fromisoformat(self.created_at)
                self.seller_confirmation_deadline = (created + timedelta(hours=24)).isoformat()
            except ValueError:
                self.seller_confirmation_deadline = None

    def transition(self, target: FulfillmentStatus, *, reason: str, actor: str) -> dict[str, Any]:
        if target not in ALLOWED_TRANSITIONS.get(self.fulfillment_status, set()):
            raise InvalidTransitionError(f"{self.fulfillment_status} -> {target} is not allowed")
        previous = self.fulfillment_status
        self.fulfillment_status = target
        self.version += 1
        history = {
            "from": previous,
            "to": target,
            "reason": reason,
            "actor": actor,
            "version": self.version,
            "occurred_at": datetime.now(UTC).isoformat(),
        }
        self.status_history.append(history)
        return history
