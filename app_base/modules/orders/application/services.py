from app_base.core.errors import DiddiShopError
from app_base.core.outbox import OutboxMessage, append_outbox, new_outbox_message
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
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
        await append_outbox(self.outbox, new_outbox_message(
            event_type=f"order.{target.value.lower()}",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={"order_id": order.id, "shop_id": order.shop_id, "history": history},
        ))
        return order

    async def apply_payment_event(self, order_id: str, event_type: str, payload: dict) -> Order:
        order = await self.get(order_id)
        if event_type == "payment.succeeded":
            order.payment_status = PaymentStatus.HELD
            if order.fulfillment_status == FulfillmentStatus.PAYMENT_PENDING:
                return await self.transition(order_id, FulfillmentStatus.TO_CONFIRM, "payment.succeeded", "diddipay")
            await self.repository.save(order)
            return order
        if event_type == "payment.failed":
            order.payment_status = PaymentStatus.PENDING
            if order.fulfillment_status == FulfillmentStatus.PAYMENT_PENDING:
                return await self.transition(order_id, FulfillmentStatus.CANCELLED, "payment.failed", "diddipay")
        if event_type == "payment.refunded":
            order.payment_status = PaymentStatus.PARTIALLY_REFUNDED if payload.get("partial") else PaymentStatus.REFUNDED
        if event_type == "seller.release.completed":
            order.payment_status = PaymentStatus.RELEASED
        await self.repository.save(order)
        return order
