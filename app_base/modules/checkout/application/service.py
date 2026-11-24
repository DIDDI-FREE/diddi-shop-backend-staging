from dataclasses import dataclass

from app_base.core.outbox import OutboxMessage, new_outbox_message
from app_base.modules.checkout.domain_interfaces import (
    CheckoutPaymentPort,
    CheckoutPricingPort,
    CheckoutRewardsPort,
)


@dataclass
class CheckoutService:
    pricing: CheckoutPricingPort
    payment: CheckoutPaymentPort
    rewards: CheckoutRewardsPort | None
    outbox: list[OutboxMessage]

    async def validate(self, cart_id: str, customer_id: str, idempotency_key: str) -> dict:
        priced = await self.pricing.price(cart_id, customer_id)
        reward = await self.rewards.quote_and_reserve(priced, f"checkout:{cart_id}") if self.rewards else None
        payment = await self.payment.create_payment({"pricing": priced, "reward": reward}, idempotency_key)
        checkout_id = payment["checkout_id"]
        self.outbox.append(new_outbox_message(
            "checkout.created", "checkout", checkout_id,
            {"checkout_id": checkout_id, "customer_id": customer_id, "cart_id": cart_id},
        ))
        return {"checkout_id": checkout_id, "payment": payment, "reward": reward}
