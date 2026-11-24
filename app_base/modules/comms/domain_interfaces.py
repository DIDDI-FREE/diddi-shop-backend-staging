from typing import Protocol


class CommunicationPort(Protocol):
    async def enqueue_order_notification(self, event: dict, operation_id: str) -> None: ...
