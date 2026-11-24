from uuid import uuid4

from app_base.modules.cart.domain import Cart


class InMemoryCartRepository:
    def __init__(self):
        self.items: dict[str, Cart] = {}

    async def get_or_create(self, customer_id: str) -> Cart:
        if customer_id not in self.items:
            self.items[customer_id] = Cart(str(uuid4()), customer_id)
        return self.items[customer_id]

    async def save(self, cart: Cart) -> None:
        self.items[cart.customer_id] = cart
