from app_base.core.errors import NotFoundError
from app_base.core.outbox import OutboxMessage, append_outbox, new_outbox_message
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.orders.domain.interfaces import OrderRepository
from app_base.modules.rewards.application import RewardsService


class OrderService:
    def __init__(self, repository: OrderRepository, outbox: list[OutboxMessage], rewards: RewardsService | None = None):
        self.repository = repository
        self.outbox = outbox
        self.rewards = rewards

    async def get(self, order_id: str) -> Order:
        order = await self.repository.get(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        return order

    async def list_for_shop(self, shop_id: str, *, status: FulfillmentStatus | None = None) -> list[Order]:
        orders = await self.repository.list_for_shop(shop_id)
        if status is not None:
            orders = [order for order in orders if order.fulfillment_status == status]
        return orders

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
                await self._confirm_reward(order, payload)
                return await self.transition(order_id, FulfillmentStatus.TO_CONFIRM, "payment.succeeded", "diddipay")
            await self.repository.save(order)
            return order
        if event_type == "payment.failed":
            order.payment_status = PaymentStatus.PENDING
            await self._release_reward(order)
            if order.fulfillment_status == FulfillmentStatus.PAYMENT_PENDING:
                return await self.transition(order_id, FulfillmentStatus.CANCELLED, "payment.failed", "diddipay")
        if event_type == "payment.refunded":
            order.payment_status = PaymentStatus.PARTIALLY_REFUNDED if payload.get("partial") else PaymentStatus.REFUNDED
            await self._correct_reward(order, payload)
        if event_type == "seller.release.completed":
            order.payment_status = PaymentStatus.RELEASED
        await self.repository.save(order)
        return order

    async def _release_reward(self, order: Order) -> None:
        if self.rewards is None or not order.metadata.get("rewards"):
            return
        reward = self.rewards.from_metadata(order.metadata["rewards"])
        if reward.consumption_id:
            return
        await self.rewards.release(reward)

    async def _confirm_reward(self, order: Order, payload: dict) -> None:
        if self.rewards is None or not order.metadata.get("rewards"):
            return
        reward = self.rewards.from_metadata(order.metadata["rewards"])
        if reward.consumption_id:
            return
        result = await self.rewards.consume(
            reward,
            order.id,
            client_paid_minor=int(payload.get("amount_minor", order.total_minor)),
            professional_payout_minor=int(order.metadata.get("professional_payout_minor", 0)),
            diddi_contribution_minor=reward.discount_minor,
            payment_reference=payload.get("payment_reference") or payload.get("payment_intent_id"),
        )
        order.metadata["rewards"] = self.rewards.to_metadata(reward)
        order.metadata["rewards"]["consumption_id"] = result.get("consumption_id")

    async def _correct_reward(self, order: Order, payload: dict) -> None:
        if self.rewards is None or not order.metadata.get("rewards"):
            return
        reward = self.rewards.from_metadata(order.metadata["rewards"])
        if not reward.consumption_id:
            return
        amount = int(payload.get("amount_minor", reward.discount_minor))
        await self.rewards.correct(
            reward,
            payload.get("reason", "payment_refunded"),
            amount,
            payload.get("payment_reference") or payload.get("refund_id"),
            operation_id=payload.get("refund_id") or "1",
        )
