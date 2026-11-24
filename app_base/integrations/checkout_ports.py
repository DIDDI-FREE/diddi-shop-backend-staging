from app_base.integrations.diddipay import DiddiPayAdapter
from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.shared_kernel.contracts.payments import PaymentIntentCommand


class DiddiPayPaymentIntentPort:
    def __init__(self, adapter: DiddiPayAdapter):
        self.adapter = adapter

    async def create(self, checkout_id: str, amount_minor: int, idempotency_key: str) -> dict:
        return await self.adapter.create_payment_intent(PaymentIntentCommand(
            checkout_id=checkout_id,
            business_reference=f"diddishop:checkout:{checkout_id}",
            amount_minor=amount_minor,
            idempotency_key=idempotency_key,
        ))


class DiddiSendDeliveryQuotePort:
    def __init__(self, adapter: DiddiSendAdapter):
        self.adapter = adapter

    async def quote(self, shop_id: str, lines: list[dict], delivery_context: dict | None = None) -> int:
        serializable = [
            {"product_id": line["product"].id, "quantity": line["quantity"], "declared_value": line["product"].price_minor * line["quantity"]}
            for line in lines
        ]
        return await self.adapter.quote(shop_id, serializable, delivery_context)
