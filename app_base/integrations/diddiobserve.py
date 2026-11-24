from app_base.integrations.base import ServiceAdapter


class DiddiObserveAdapter(ServiceAdapter):
    async def export(self, payload: dict) -> None:
        response = await self.request("POST", "/internal/v1/telemetry", json=payload)
        response.raise_for_status()
