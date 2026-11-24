from app_base.modules.orders.domain.entities import Order


class InMemoryOrderRepository:
    def __init__(self):
        self._orders: dict[str, Order] = {}

    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order
