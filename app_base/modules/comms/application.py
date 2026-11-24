from dataclasses import dataclass


@dataclass
class CommunicationService:
    adapter: object

    async def open_conversation(
        self,
        *,
        owner_service: str,
        task_type: str,
        task_id: str,
        idempotency_key: str | None = None,
    ) -> dict:
        return await self.adapter.open_conversation(
            owner_service,
            task_type,
            task_id,
            idempotency_key,
        )
