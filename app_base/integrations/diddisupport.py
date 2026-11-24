from app_base.integrations.base import ServiceAdapter


class DiddiSupportAdapter(ServiceAdapter):
    async def create_case(self, payload: dict, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            "/support/v1/internal/cases",
            headers={"Idempotency-Key": idempotency_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_context(self, origin_service: str, resource_type: str, resource_id: str) -> dict:
        response = await self.request(
            "GET",
            f"/support/v1/internal/context/{origin_service}/{resource_type}/{resource_id}",
        )
        response.raise_for_status()
        return response.json()
