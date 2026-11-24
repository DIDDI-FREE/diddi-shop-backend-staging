from app_base.core.errors import DiddiShopError
from app_base.core.outbox import OutboxMessage, new_outbox_message
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order
from app_base.modules.orders.domain.interfaces import OrderRepository


class OrderService:
    def __init__(self, repository: OrderRepository, outbox: list[OutboxMessage]):
        self.repository = repository
        self.outbox = outbox

    async def get(self, order_id: str) -> Order:
        order = await self.repository.get(order_id)
        if order is None:
            raise DiddiShopError(f"Order {order_id} not found")
        return order

    async def transition(self, order_id: str, target: FulfillmentStatus, reason: str, actor: str) -> Order:
        order = await self.get(order_id)
        history = order.transition(target, reason=reason, actor=actor)
        await self.repository.save(order)
        self.outbox.append(new_outbox_message(
            event_type=f"order.{target.value.lower()}",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={"order_id": order.id, "shop_id": order.shop_id, "history": history},
        ))
        return order
