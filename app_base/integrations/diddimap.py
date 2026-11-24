from app_base.integrations.base import ServiceAdapter


class DiddiMapAdapter(ServiceAdapter):
    async def validate_address(self, payload: dict) -> dict:
        response = await self.request("POST", "/internal/v1/addresses/validate", json=payload)
        response.raise_for_status()
        return response.json()
