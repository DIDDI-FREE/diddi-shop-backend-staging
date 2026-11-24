from typing import Protocol


class SupportDecisionPort(Protocol):
    async def open_case(self, order_id: str, claim_id: str, reason: str, idempotency_key: str) -> None: ...


class ClaimFinancialPort(Protocol):
    async def refund(self, order_id: str, amount_minor: int, idempotency_key: str) -> None: ...


class ClaimRepository(Protocol):
    async def save(self, claim: dict) -> None: ...
    async def get(self, claim_id: str) -> dict | None: ...
