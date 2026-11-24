from app_base.integrations.base import ServiceAdapter


class DiddiSupportAdapter(ServiceAdapter):
    async def create_case(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request("POST", "/internal/v1/cases", headers={"Idempotency-Key": idempotency_key}, json=payload)
        response.raise_for_status()
        return response.json()
