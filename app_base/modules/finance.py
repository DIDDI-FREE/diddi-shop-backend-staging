from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app_base.core.errors import ConflictError
from app_base.modules.claims.domain import Claim, ClaimDecision, ClaimStatus
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus


class FinancialPort:
    async def refund(self, payment_intent_id: str, amount_minor: int, idempotency_key: str) -> None:
        raise NotImplementedError

    async def release(self, order_id: str, amount_minor: int, idempotency_key: str) -> None:
        raise NotImplementedError


class FinanceService:
    def __init__(self, orders, claims, financial: FinancialPort, products=None, delivery=None):
        self.orders = orders
        self.claims = claims
        self.financial = financial
        self.products = products
        self.delivery = delivery

    async def cancel(self, order_id: str, reason: str) -> Order:
        order = await self.orders.get(order_id)
        if order.fulfillment_status in {FulfillmentStatus.PICKED_UP, FulfillmentStatus.IN_TRANSIT, FulfillmentStatus.DELIVERED}:
            raise ConflictError("order cannot be cancelled after pickup")
        order.transition(FulfillmentStatus.CANCELLED, reason=reason, actor="buyer")
        order.payment_status = PaymentStatus.REFUND_PENDING
        if self.products:
            for line in order.metadata.get("lines", []):
                await self.products.apply_stock(line["product_id"], line["quantity"], f"cancel:{order.id}:product:{line['product_id']}")
        if self.delivery and order.delivery_id:
            await self.delivery.cancel_delivery(order.delivery_id, f"shop:cancel-delivery:{order.id}:1")
        await self.orders.repository.save(order)
        payment_id = order.metadata.get("payment_intent_id", order.checkout_id)
        await self.financial.refund(payment_id, order.total_minor, f"shop:refund:{order.id}:1")
        return order

    async def expire_seller_confirmation(self, order_id: str) -> Order:
        return await self.cancel(order_id, "seller_unresponsive")

    async def open_claim(self, order_id: str, customer_id: str, reason: str, now: datetime | None = None) -> Claim:
        order = await self.orders.get(order_id)
        now = now or datetime.now(timezone.utc)
        if order.fulfillment_status != FulfillmentStatus.DELIVERED:
            raise ConflictError("claim requires delivered order")
        delivered_at = order.metadata.get("delivered_at")
        if delivered_at and now - delivered_at > timedelta(hours=72):
            raise ConflictError("claim window expired")
        if await self.claims.get_open_for_order(order_id):
            raise ConflictError("claim already open")
        claim = Claim(str(uuid4()), order_id, customer_id, reason, now)
        order.transition(FulfillmentStatus.DISPUTED, reason="claim.opened", actor=customer_id)
        order.payment_status = PaymentStatus.RELEASE_BLOCKED
        await self.claims.save(claim)
        await self.orders.repository.save(order)
        return claim

    async def decide(self, claim_id: str, decision: ClaimDecision, amount_to_refund: int = 0) -> Claim:
        claim = await self.claims.get(claim_id)
        if claim is None or claim.status != ClaimStatus.OPEN:
            raise ConflictError("claim is not open")
        order = await self.orders.get(claim.order_id)
        claim.status = ClaimStatus.DECIDED
        claim.decision = decision
        claim.amount_to_refund = amount_to_refund
        claim.decided_at = datetime.now(timezone.utc)
        if decision in {ClaimDecision.BUYER, ClaimDecision.PARTIAL}:
            amount = amount_to_refund or order.total_minor
            order.payment_status = PaymentStatus.REFUND_PENDING
            await self.financial.refund(order.checkout_id, amount, f"shop:refund:{order.id}:claim:{claim.id}")
        else:
            order.payment_status = PaymentStatus.RELEASE_PENDING
            await self.financial.release(order.id, order.metadata.get("net_seller_minor", order.total_minor), f"shop:release:{order.id}:1")
        order.transition(FulfillmentStatus.CLOSED, reason=f"claim.decided:{decision.value}", actor="support")
        await self.claims.save(claim)
        await self.orders.repository.save(order)
        return claim

    async def release_if_eligible(self, order_id: str, now: datetime | None = None) -> Order:
        order = await self.orders.get(order_id)
        if order.fulfillment_status != FulfillmentStatus.DELIVERED:
            raise ConflictError("release requires delivered order")
        if await self.claims.get_open_for_order(order_id):
            order.payment_status = PaymentStatus.RELEASE_BLOCKED
            await self.orders.repository.save(order)
            return order
        eligible_at = order.metadata.get("release_eligible_at")
        now = now or datetime.now(timezone.utc)
        if eligible_at and now < eligible_at:
            raise ConflictError("release delay has not elapsed")
        order.payment_status = PaymentStatus.RELEASE_PENDING
        await self.financial.release(order.id, order.metadata.get("net_seller_minor", order.total_minor), f"shop:release:{order.id}:1")
        await self.orders.repository.save(order)
        return order
