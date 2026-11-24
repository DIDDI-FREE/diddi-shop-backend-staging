from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app_base.core.errors import InvalidTransitionError


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
    FulfillmentStatus.READY_FOR_PICKUP: {FulfillmentStatus.PICKED_UP, FulfillmentStatus.CANCELLED},
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
    currency: str = "XAF"
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.PAYMENT_PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    delivery_id: str | None = None
    version: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, target: FulfillmentStatus, *, reason: str, actor: str) -> dict[str, Any]:
        if target not in ALLOWED_TRANSITIONS.get(self.fulfillment_status, set()):
            raise InvalidTransitionError(f"{self.fulfillment_status} -> {target} is not allowed")
        previous = self.fulfillment_status
        self.fulfillment_status = target
        self.version += 1
        return {"from": previous, "to": target, "reason": reason, "actor": actor, "version": self.version}
