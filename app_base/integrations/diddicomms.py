from app_base.integrations.base import ServiceAdapter


class DiddiCommsAdapter(ServiceAdapter):
    async def create_task(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request("POST", "/internal/v1/tasks", headers={"Idempotency-Key": idempotency_key}, json=payload)
        response.raise_for_status()
        return response.json()
