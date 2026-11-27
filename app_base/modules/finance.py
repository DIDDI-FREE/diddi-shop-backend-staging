from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app_base.core.errors import (
    ClaimAlreadyOpenError,
    ClaimWindowExpiredError,
    ConflictError,
    DeliveryAlreadyPickedUpError,
    OrderNotCancellableError,
)
from app_base.modules.claims.domain import Claim, ClaimDecision, ClaimStatus

SUPPORTED_REFUND_METHODS = {"wave", "mtn_momo", "orange_money"}
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.rewards.application import RewardsService


class FinancialPort:
    async def refund(self, payment_intent_id: str, amount_minor: int, idempotency_key: str) -> dict | None:
        raise NotImplementedError

    async def release(self, order_id: str, amount_minor: int, idempotency_key: str) -> None:
        raise NotImplementedError


class FinanceService:
    def __init__(
        self,
        orders,
        claims,
        financial: FinancialPort,
        products=None,
        delivery=None,
        seller_release_enabled: bool = False,
        rewards: RewardsService | None = None,
        claim_window_hours: int = 72,
    ):
        self.orders = orders
        self.claims = claims
        self.financial = financial
        self.products = products
        self.delivery = delivery
        self.seller_release_enabled = seller_release_enabled
        self.rewards = rewards
        self.claim_window_hours = claim_window_hours

    async def cancel(self, order_id: str, reason: str) -> Order:
        order = await self.orders.get(order_id)
        if order.fulfillment_status == FulfillmentStatus.CANCELLED:
            return order
        if order.fulfillment_status in {FulfillmentStatus.PICKED_UP, FulfillmentStatus.IN_TRANSIT, FulfillmentStatus.DELIVERED}:
            if order.fulfillment_status == FulfillmentStatus.PICKED_UP:
                raise DeliveryAlreadyPickedUpError("delivery has already been picked up")
            raise OrderNotCancellableError("order cannot be cancelled after pickup")
        if order.payment_status == PaymentStatus.PENDING and self.rewards and order.metadata.get("rewards"):
            reward = self.rewards.from_metadata(order.metadata["rewards"])
            if not reward.consumption_id:
                await self.rewards.release(reward)
        order.transition(FulfillmentStatus.CANCELLED, reason=reason, actor="buyer")
        order.payment_status = PaymentStatus.REFUND_PENDING
        if self.products:
            for line in order.metadata.get("lines", []):
                await self.products.apply_stock(line["product_id"], line["quantity"], f"cancel:{order.id}:product:{line['product_id']}")
        if self.delivery and order.delivery_id:
            await self.delivery.cancel_delivery(order.delivery_id, f"shop:cancel-delivery:{order.id}:1")
        await self.orders.repository.save(order)
        payment_id = order.metadata.get("payment_intent_id", order.checkout_id)
        if order.metadata.get("refund_operation") != f"shop:refund:{order.id}:1":
            operation = f"shop:refund:{order.id}:1"
            await self.financial.refund(payment_id, order.total_minor, operation)
            order.metadata["refund_operation"] = operation
            await self.orders.repository.save(order)
        return order

    async def expire_seller_confirmation(self, order_id: str) -> Order:
        return await self.cancel(order_id, "seller_unresponsive")

    async def open_claim(
        self,
        order_id: str,
        customer_id: str,
        reason: str,
        now: datetime | None = None,
        *,
        reason_code: str = "other",
        evidence_file_ids: list[str] | None = None,
    ) -> Claim:
        order = await self.orders.get(order_id)
        now = now or datetime.now(UTC)
        if order.fulfillment_status != FulfillmentStatus.DELIVERED:
            raise ConflictError("claim requires delivered order")
        delivered_at = order.metadata.get("delivered_at")
        if isinstance(delivered_at, str):
            delivered_at = datetime.fromisoformat(delivered_at)
        claim_deadline = delivered_at + timedelta(hours=self.claim_window_hours) if delivered_at else None
        if claim_deadline and now > claim_deadline:
            raise ClaimWindowExpiredError("claim window expired")
        if await self.claims.get_open_for_order(order_id):
            raise ClaimAlreadyOpenError("claim already open")
        claim = Claim(
            str(uuid4()), order_id, customer_id, reason, now,
            reason_code=reason_code,
            evidence_file_ids=list(evidence_file_ids or []),
            delivered_at=delivered_at,
            claim_deadline=claim_deadline,
        )
        order.transition(FulfillmentStatus.DISPUTED, reason="claim.opened", actor=customer_id)
        if self.seller_release_enabled:
            order.payment_status = PaymentStatus.RELEASE_BLOCKED
        await self.claims.save(claim)
        await self.orders.repository.save(order)
        return claim

    async def decide(self, claim_id: str, decision: ClaimDecision, amount_to_refund: int = 0) -> Claim:
        claim = await self.claims.get(claim_id)
        if claim is None or claim.status != ClaimStatus.OPEN:
            raise ConflictError("claim is not open")
        order = await self.orders.get(claim.order_id)
        if decision in {ClaimDecision.BUYER, ClaimDecision.PARTIAL} and amount_to_refund > order.total_minor:
            raise ConflictError("refund exceeds order total")
        claim.status = ClaimStatus.DECIDED
        claim.decision = decision
        claim.amount_to_refund = amount_to_refund
        claim.decided_at = datetime.now(UTC)
        if decision in {ClaimDecision.BUYER, ClaimDecision.PARTIAL}:
            amount = amount_to_refund or order.total_minor
            order.payment_status = PaymentStatus.REFUND_PENDING
            payment_id = order.metadata.get("payment_intent_id", order.checkout_id)
            operation = f"shop:refund:{order.id}:claim:{claim.id}"
            if order.metadata.get("refund_operation") != operation:
                refund = await self.financial.refund(payment_id, amount, operation)
                order.metadata["refund_operation"] = operation
                claim.refund_status = str((refund or {}).get("status", "pending")).lower()
                raw_refund_method = (
                    (refund or {}).get("payment_method")
                    or order.metadata.get("payment_method")
                    or order.metadata.get("delivery_request", {}).get("payment_method")
                )
                claim.refund_method = (
                    str(raw_refund_method).lower()
                    if str(raw_refund_method).lower() in SUPPORTED_REFUND_METHODS
                    else None
                )
                refund_reference = (refund or {}).get("refund_id")
                claim.refund_reference_masked = f"****{str(refund_reference)[-4:]}" if refund_reference else None
                claim.refunded_at = datetime.now(UTC) if claim.refund_status == "succeeded" else None
        else:
            if self.seller_release_enabled:
                order.payment_status = PaymentStatus.RELEASE_PENDING
                operation = f"shop:release:{order.id}:1"
                if order.metadata.get("release_operation") != operation:
                    await self.financial.release(order.id, order.metadata.get("net_seller_minor", order.total_minor), operation)
                    order.metadata["release_operation"] = operation
        order.transition(FulfillmentStatus.CLOSED, reason=f"claim.decided:{decision.value}", actor="support")
        await self.claims.save(claim)
        await self.orders.repository.save(order)
        return claim

    async def release_if_eligible(self, order_id: str, now: datetime | None = None) -> Order:
        order = await self.orders.get(order_id)
        if not self.seller_release_enabled:
            return order
        if order.fulfillment_status != FulfillmentStatus.DELIVERED:
            raise ConflictError("release requires delivered order")
        if await self.claims.get_open_for_order(order_id):
            order.payment_status = PaymentStatus.RELEASE_BLOCKED
            await self.orders.repository.save(order)
            return order
        eligible_at = order.metadata.get("release_eligible_at")
        now = now or datetime.now(UTC)
        if eligible_at and now < eligible_at:
            raise ConflictError("release delay has not elapsed")
        order.payment_status = PaymentStatus.RELEASE_PENDING
        operation = f"shop:release:{order.id}:1"
        if order.metadata.get("release_operation") != operation:
            await self.financial.release(order.id, order.metadata.get("net_seller_minor", order.total_minor), operation)
            order.metadata["release_operation"] = operation
        await self.orders.repository.save(order)
        return order

    async def handle_delivery_failure(self, order_id: str, event_type: str) -> Order:
        order = await self.orders.get(order_id)
        if order.payment_status in {PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED}:
            return order
        operation = f"shop:refund:{order.id}:delivery"
        order.payment_status = PaymentStatus.REFUND_PENDING
        payment_id = order.metadata.get("payment_intent_id", order.checkout_id)
        if order.metadata.get("refund_operation") != operation:
            await self.financial.refund(payment_id, order.total_minor, operation)
            order.metadata["refund_operation"] = operation
        await self.orders.repository.save(order)
        return order
