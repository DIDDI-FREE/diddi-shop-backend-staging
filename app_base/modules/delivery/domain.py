from dataclasses import dataclass
from enum import StrEnum


class DeliveryStatus(StrEnum):
    REQUESTED = "requested"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


@dataclass
class DeliveryProjection:
    id: str
    order_id: str
    status: DeliveryStatus
    proof_ref: str | None = None
    tracking: dict | None = None
    courier: dict | None = None
    dropoff_code: str | None = None
    position: dict | None = None

    def __post_init__(self) -> None:
        self.status = DeliveryStatus(self.status)
