from app_base.modules.orders.domain.entities import Order


class InMemoryOrderRepository:
    def __init__(self):
        self._orders: dict[str, Order] = {}

    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def create(self, order: Order) -> None:
        if order.id in self._orders:
            raise ValueError(f"order {order.id} already exists")
        self._orders[order.id] = order

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order

    async def list_for_shop(self, shop_id: str) -> list[Order]:
        return [order for order in self._orders.values() if order.shop_id == shop_id]
