from app_base.modules.delivery.domain import DeliveryProjection


class InMemoryDeliveryRepository:
    def __init__(self):
        self.items: dict[str, DeliveryProjection] = {}

    async def save(self, delivery: DeliveryProjection) -> None:
        self.items[delivery.order_id] = delivery

    async def get_by_order(self, order_id: str) -> DeliveryProjection | None:
        return self.items.get(order_id)
