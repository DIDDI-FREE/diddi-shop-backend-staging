from typing import Protocol


class SupportContextPort(Protocol):
    async def build_order_context(self, order_id: str) -> dict: ...


class SupportCasePort(Protocol):
    async def open_claim_case(self, claim: dict, operation_id: str) -> str: ...
