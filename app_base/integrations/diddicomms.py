from app_base.integrations.base import ServiceAdapter


class DiddiCommsAdapter(ServiceAdapter):
    async def create_task(self, payload: dict, idempotency_key: str) -> dict:
        owner_service = payload.get("owner_service", "diddishop")
        task_type = payload.get("task_type", "order")
        task_id = payload.get("task_id") or payload.get("event_id")
        response = await self.request(
            "POST",
            f"/comms/v1/tasks/{owner_service}/{task_type}/{task_id}/conversation",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
