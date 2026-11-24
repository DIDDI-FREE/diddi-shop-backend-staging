from typing import Protocol


class CheckoutPricingPort(Protocol):
    async def price(self, cart_id: str, customer_id: str) -> dict: ...


class CheckoutPaymentPort(Protocol):
    async def create_payment(self, checkout: dict, idempotency_key: str) -> dict: ...


class CheckoutRewardsPort(Protocol):
    async def quote_and_reserve(
        self,
        customer_id: str,
        campaign_id: str,
        amount_initial_minor: int,
        operation_id: str,
    ) -> dict: ...
