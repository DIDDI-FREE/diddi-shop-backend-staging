from app_base.integrations.base import ServiceAdapter
from app_base.core.request_context import get_request_context
from app_base.shared_kernel.contracts.delivery import DeliveryCommand, DeliveryRequest


class DiddiSendAdapter(ServiceAdapter):
    async def quote(self, shop_id: str, lines: list[dict]) -> int:
        response = await self.request(
            "POST", "/v1/deliveries/quote",
            json={"origin_module": "diddishop", "shop_id": shop_id, "lines": lines},
        )
        response.raise_for_status()
        data = response.json()
        return int(data.get("quoted_price", data.get("amount_minor", data.get("delivery_fee", 0))))

    async def create_delivery(self, command: DeliveryCommand, payload: dict) -> dict:
        request = DeliveryRequest(
            order_reference=payload["order_reference"],
            idempotency_key=command.idempotency_key,
            sender_user_id=payload.get("sender_user_id", "diddishop-system"),
            customer_user_id=payload["customer_user_id"],
            recipient_name=payload["recipient_name"],
            recipient_phone=payload["recipient_phone"],
            sender_phone=payload.get("sender_phone"),
            pickup_location=payload["pickup_location"],
            pickup_address=payload["pickup_address"],
            dropoff_location=payload["dropoff_location"],
            dropoff_address=payload["dropoff_address"],
            package=payload["package"],
            ready_at=payload.get("ready_at"),
            quoted_price=str(payload["quoted_price"]),
            financial_breakdown=payload.get("financial_breakdown"),
        )
        context = get_request_context()
        headers = {"Idempotency-Key": command.idempotency_key}
        if context:
            headers["X-Request-ID"] = context.request_id
        response = await self.request(
            "POST", "/v1/deliveries",
            headers=headers,
            json=request.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    async def cancel_delivery(self, delivery_id: str, idempotency_key: str) -> None:
        response = await self.request("POST", f"/v1/deliveries/{delivery_id}/cancel", headers={"Idempotency-Key": idempotency_key})
        response.raise_for_status()
