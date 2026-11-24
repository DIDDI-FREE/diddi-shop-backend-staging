from dataclasses import dataclass
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


class ClaimRepository:
    async def save(self, claim: Claim) -> None:
        raise NotImplementedError

    async def get(self, claim_id: str) -> Claim | None:
        raise NotImplementedError

    async def get_open_for_order(self, order_id: str) -> Claim | None:
        raise NotImplementedError
