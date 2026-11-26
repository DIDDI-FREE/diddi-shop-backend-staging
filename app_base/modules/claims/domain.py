from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ClaimStatus(StrEnum):
    OPEN = "open"
    DECIDED = "decided"


class ClaimDecision(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"
    PARTIAL = "partial"
    REJECTED = "rejected"


@dataclass
class Claim:
    id: str
    order_id: str
    customer_id: str
    reason: str
    opened_at: datetime
    status: ClaimStatus = ClaimStatus.OPEN
    decision: ClaimDecision | None = None
    amount_to_refund: int = 0
    decided_at: datetime | None = None
    reason_code: str = "other"
    evidence_file_ids: list[str] = field(default_factory=list)
    delivered_at: datetime | None = None
    claim_deadline: datetime | None = None
    refund_status: str = "not_requested"
    refund_method: str | None = None
    refund_reference_masked: str | None = None
    refunded_at: datetime | None = None


class ClaimRepository:
    async def save(self, claim: Claim) -> None:
        raise NotImplementedError

    async def get(self, claim_id: str) -> Claim | None:
        raise NotImplementedError

    async def get_open_for_order(self, order_id: str) -> Claim | None:
        raise NotImplementedError

    async def get_for_order(self, order_id: str) -> Claim | None:
        raise NotImplementedError
