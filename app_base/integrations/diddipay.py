from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.payments import PaymentIntentCommand


class DiddiPayAdapter(ServiceAdapter):
    async def create_payment_intent(self, command: PaymentIntentCommand) -> dict:
        response = await self.request(
            "POST", "/payment-intents",
            headers={"Idempotency-Key": command.idempotency_key},
            json=command.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    async def refund(self, order_id: str, amount_minor: int, idempotency_key: str) -> dict:
        response = await self.request(
            "POST", f"/payment-intents/{order_id}/refunds",
            headers={"Idempotency-Key": idempotency_key},
            json={"amount_minor": amount_minor, "reason": "diddishop_order"},
        )
        response.raise_for_status()
        return response.json()

    async def request_release(self, order_id: str, amount_minor: int, idempotency_key: str) -> dict:
        raise NotImplementedError("Marketplace seller release must be added to the DiddiPay contract")

    async def release(self, order_id: str, amount_minor: int, idempotency_key: str) -> None:
        await self.request_release(order_id, amount_minor, idempotency_key)
