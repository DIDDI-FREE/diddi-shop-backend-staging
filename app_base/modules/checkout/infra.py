from app_base.modules.checkout.domain import Checkout


class InMemoryCheckoutRepository:
    def __init__(self):
        self.items: dict[str, Checkout] = {}

    async def save(self, checkout: Checkout) -> None:
        self.items[checkout.id] = checkout

    async def get(self, checkout_id: str) -> Checkout | None:
        return self.items.get(checkout_id)

    async def list_for_customer(self, customer_id: str) -> list[Checkout]:
        return [checkout for checkout in self.items.values() if checkout.customer_id == customer_id]
