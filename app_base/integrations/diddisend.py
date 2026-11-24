from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryCommand


class DiddiSendAdapter(ServiceAdapter):
    async def create_delivery(self, command: DeliveryCommand, payload: dict) -> dict:
        response = await self.request(
            "POST", "/v1/deliveries",
            headers={"Idempotency-Key": command.idempotency_key},
            json={**payload, "origin_service": command.origin_service, "prepaid_by_origin": command.prepaid_by_origin},
        )
        response.raise_for_status()
        return response.json()

    async def cancel_delivery(self, delivery_id: str, idempotency_key: str) -> None:
        response = await self.request("POST", f"/v1/deliveries/{delivery_id}/cancel", headers={"Idempotency-Key": idempotency_key})
        response.raise_for_status()
