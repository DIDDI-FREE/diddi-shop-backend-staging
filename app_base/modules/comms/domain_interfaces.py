from typing import Protocol


class CommunicationPort(Protocol):
    async def open_conversation(
        self,
        *,
        owner_service: str,
        task_type: str,
        task_id: str,
        idempotency_key: str | None = None,
    ) -> dict: ...
