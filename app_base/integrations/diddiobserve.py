from app_base.integrations.base import ServiceAdapter


class DiddiObserveAdapter(ServiceAdapter):
    async def export(self, payload: dict, path: str = "/v1/logs") -> None:
        response = await self.request("POST", path, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
