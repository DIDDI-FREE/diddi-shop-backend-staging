from urllib.parse import quote
from uuid import UUID

from app_base.integrations.base import ServiceAdapter


class DiddiCommsAdapter(ServiceAdapter):
    async def open_conversation(
        self,
        owner_service: str,
        task_type: str,
        task_id: str,
        idempotency_key: str | None = None,
    ) -> dict:
        """Open or retrieve a conversation; this route does not send notifications."""
        UUID(task_id)
        response = await self.request(
            "POST",
            "/comms/v1/tasks/"
            f"{quote(owner_service, safe='')}/{quote(task_type, safe='')}/{quote(task_id, safe='')}/conversation",
            headers={"Idempotency-Key": idempotency_key} if idempotency_key else None,
        )
        response.raise_for_status()
        return response.json()
