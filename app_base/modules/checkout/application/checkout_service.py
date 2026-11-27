import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app_base.core.errors import ConflictError
from app_base.core.outbox import OutboxMessage, append_outbox, new_outbox_message
from app_base.modules.cart.domain import CartRepository
from app_base.modules.catalog.domain import ProductRepository
from app_base.modules.checkout.domain import Checkout, CheckoutRepository, CheckoutStatus
from app_base.modules.orders.domain.entities import Order
from app_base.modules.orders.domain.interfaces import OrderRepository
from app_base.modules.rewards.application import RewardsService
from app_base.modules.shops.domain import ShopRepository
from app_base.shared_kernel.contracts.payments import (
    DEFAULT_PAYMENT_RETURN_URL,
    PaymentReturnOptions,
    require_customer_phone,
    require_payment_return,
    valid_customer_phone,
)

logger = logging.getLogger(__name__)


def _technical_sender_email(phone: str, configured_email: str) -> str:
    """Return a stable non-personal email when the sender has no mailbox."""
    if configured_email.strip():
        return configured_email.strip()
    digits = "".join(character for character in phone if character.isdigit())
    return f"{digits or 'diddishop-system'}@diddifree.com"


class DeliveryQuotePort:
    async def quote(self, shop_id: str, cart_lines: list[dict], delivery_context: dict | None = None) -> int:
        raise NotImplementedError


class PaymentIntentPort:
    async def create(self, checkout_id: str, amount_minor: int, idempotency_key: str) -> dict:
        raise NotImplementedError

    async def create_with_options(
        self,
        checkout_id: str,
        amount_minor: int,
        idempotency_key: str,
        *,
        payment_method: str = "wave",
        return_url: str | None = None,
        return_target: str | None = None,
        customer_phone: str | None = None,
    ) -> dict:
        raise NotImplementedError("Payment ports must explicitly handle customer_phone")


@dataclass
class CheckoutApplicationService:
    carts: CartRepository
    products: ProductRepository
    checkouts: CheckoutRepository
    orders: OrderRepository
    delivery_quotes: DeliveryQuotePort
    payments: PaymentIntentPort
    outbox: list[OutboxMessage]
    shops: ShopRepository | None = None
    rewards: RewardsService | None = None
    seller_confirmation_hours: int = 24
    diddisend_service_user_id: str = ""
    diddisend_sender_phone: str = ""
    diddisend_sender_email: str = ""
    payment_return_url: str | None = DEFAULT_PAYMENT_RETURN_URL
    payment_return_target: str | None = None

    def _payment_return(self, *sources: dict) -> PaymentReturnOptions:
        for source in sources:
            if source.get("return_url") or source.get("return_target"):
                return require_payment_return(source.get("return_url"), source.get("return_target"))
        return require_payment_return(
            None if self.payment_return_target else (self.payment_return_url or None),
            self.payment_return_target or None,
        )

    @staticmethod
    def _checkout_status_for_payment(payment: dict) -> CheckoutStatus:
        status = str(payment.get("status", "pending")).lower()
        if status in {"succeeded", "success", "paid", "completed"}:
            return CheckoutStatus.PAYMENT_SUCCEEDED
        if status in {"failed", "failure", "declined", "cancelled", "canceled"}:
            return CheckoutStatus.PAYMENT_FAILED
        return CheckoutStatus.PAYMENT_PENDING

    @staticmethod
    def _payment_failure_fields(payment: dict) -> dict:
        return {
            "payment_failure_code": payment.get("failure_code") or payment.get("code"),
            "payment_failure_message": payment.get("failure_message") or payment.get("message"),
            "payment_provider_status": payment.get("provider_status") or payment.get("status"),
        }

    async def _load_groups(self, customer_id: str) -> dict[str, list[dict]]:
        cart = await self.carts.get_or_create(customer_id)
        if not cart.lines:
            raise ConflictError("cart is empty")
        grouped: dict[str, list[dict]] = {}
        for line in cart.lines:
            product = await self.products.get(line.product_id)
            if product is None or product.status.value != "published":
                raise ConflictError("cart contains an unavailable product")
            if product.stock < line.quantity:
                raise ConflictError("cart contains insufficient stock")
            grouped.setdefault(product.shop_id, []).append({
                "product": product,
                "product_id": product.id,
                "quantity": line.quantity,
                "declared_value": product.price_minor * line.quantity,
            })
        return grouped

    async def _quote_groups(self, grouped: dict[str, list[dict]], delivery_context: dict) -> list[dict]:
        breakdowns = []
        for shop_id, lines in grouped.items():
            items_total = sum(item["product"].price_minor * item["quantity"] for item in lines)
            shop = await self.shops.get(shop_id) if self.shops is not None else None
            quote_context = dict(delivery_context)
            if shop is not None:
                quote_context.setdefault("pickup_location", {
                    "lat": shop.pickup_latitude,
                    "lng": shop.pickup_longitude,
                    "address": shop.pickup_address,
                })
            delivery_fee = await self.delivery_quotes.quote(shop_id, lines, quote_context)
            breakdowns.append({
                "shop_id": shop_id,
                "subtotal_minor": items_total,
                "delivery_fee_minor": delivery_fee,
                "discount_minor": 0,
                "total_minor": items_total + delivery_fee,
            })
        return breakdowns

    async def quote(self, customer_id: str, delivery_context: dict) -> dict:
        grouped = await self._load_groups(customer_id)
        breakdowns = await self._quote_groups(grouped, delivery_context)
        return {
            "currency": "XOF",
            "subtotal_minor": sum(item["subtotal_minor"] for item in breakdowns),
            "delivery_fee_minor": sum(item["delivery_fee_minor"] for item in breakdowns),
            "discount_minor": 0,
            "total_minor": sum(item["total_minor"] for item in breakdowns),
            "shop_breakdowns": breakdowns,
        }

    async def create(self, customer_id: str, idempotency_key: str, delivery_context: dict | None = None) -> Checkout:
        delivery_context = delivery_context or {}
        customer_phone = require_customer_phone(delivery_context.get("recipient_phone"))
        payment_return = self._payment_return(delivery_context)
        grouped = await self._load_groups(customer_id)

        checkout_id = str(uuid4())
        created_orders: list[Order] = []
        reward_reservations = []
        total = 0
        subtotal = 0
        delivery_total = 0
        discount_total = 0
        breakdowns: list[dict] = []
        try:
            for shop_id, lines in grouped.items():
                items_total = sum(item["product"].price_minor * item["quantity"] for item in lines)
                shop = await self.shops.get(shop_id) if self.shops is not None else None
                quote_context = dict(delivery_context or {})
                if shop is not None:
                    quote_context.setdefault("pickup_location", {
                        "lat": shop.pickup_latitude,
                        "lng": shop.pickup_longitude,
                        "address": shop.pickup_address,
                    })
                delivery_fee = await self.delivery_quotes.quote(shop_id, lines, quote_context or None)
                order_id = str(uuid4())
                initial_total = items_total + delivery_fee
                reward_reservation = None
                rewards_campaign_id = quote_context.get("rewards_campaign_id")
                if self.rewards is not None and rewards_campaign_id:
                    reward_reservation = await self.rewards.quote_and_reserve(
                        customer_id,
                        str(rewards_campaign_id),
                        initial_total,
                        f"diddishop:benefit-reservation:{order_id}:1",
                    )
                    if reward_reservation is not None:
                        reward_reservations.append(reward_reservation)
                reward_discount = reward_reservation.discount_minor if reward_reservation else 0
                final_total = initial_total - reward_discount
                subtotal += items_total
                delivery_total += delivery_fee
                discount_total += reward_discount
                breakdowns.append({
                    "shop_id": shop_id,
                    "subtotal_minor": items_total,
                    "delivery_fee_minor": delivery_fee,
                    "discount_minor": reward_discount,
                    "total_minor": final_total,
                })
                created_at = datetime.now(UTC)
                for item in lines:
                    await self.products.apply_stock(
                        item["product"].id,
                        -item["quantity"],
                        f"checkout:{checkout_id}:product:{item['product'].id}",
                    )
                order = Order(
                    id=order_id,
                    shop_id=shop_id,
                    checkout_id=checkout_id,
                    total_minor=final_total,
                    currency="XOF",
                    metadata={
                        "items_total": items_total,
                        "delivery_fee": delivery_fee,
                        "rewards_discount_minor": reward_discount,
                        "rewards": self.rewards.to_metadata(reward_reservation) if reward_reservation else None,
                        "lines": [
                            {
                                "product_id": item["product"].id,
                                "title": item["product"].title,
                                "unit_price_minor": item["product"].price_minor,
                                "quantity": item["quantity"],
                                "line_total_minor": item["product"].price_minor * item["quantity"],
                            }
                            for item in lines
                        ],
                        "delivery_request": {
                            **quote_context,
                            "customer_user_id": customer_id,
                            "recipient_user_id": customer_id,
                            "sender_user_id": self.diddisend_service_user_id
                            or (shop.owner_id if shop is not None else "diddishop-system"),
                            "sender_phone": self.diddisend_sender_phone,
                            "sender_email": _technical_sender_email(
                                self.diddisend_sender_phone,
                                self.diddisend_sender_email,
                            ),
                            "recipient_name": quote_context.get("recipient_name", customer_id),
                            "recipient_phone": quote_context.get("recipient_phone", "unknown"),
                            "pickup_address": quote_context.get("pickup_location", {}).get("address", ""),
                            "dropoff_address": quote_context.get("dropoff_location", {}).get("address", ""),
                            "package": {
                                "label": f"DiddiShop order {order_id}",
                                "description": "DiddiShop physical goods",
                                "category": "physical_goods",
                                "declared_value": items_total,
                            },
                            "quoted_price": delivery_fee,
                            "payment_method": quote_context.get("payment_method", "wave"),
                        },
                    },
                    created_at=created_at.isoformat(),
                    seller_confirmation_deadline=(created_at + timedelta(hours=self.seller_confirmation_hours)).isoformat(),
                )
                await self.orders.create(order)
                created_orders.append(order)
                total += order.total_minor
            payment = await self.payments.create_with_options(
                checkout_id,
                total,
                idempotency_key,
                payment_method=delivery_context.get("payment_method", "wave"),
                **payment_return.model_dump(),
                customer_phone=customer_phone,
            )
            # Inputs are owned by Shop; a missing/null upstream echo cannot erase them.
            payment["payment_method"] = delivery_context.get("payment_method", "wave")
            payment["customer_phone"] = customer_phone
            payment.update(payment_return.model_dump())
            payment = {**payment, **self._payment_failure_fields(payment)}
        except Exception:
            if self.rewards is not None:
                for reservation in reward_reservations:
                    try:
                        await self.rewards.release(reservation)
                    except Exception:
                        logger.exception(
                            "Rewards reservation release failed during checkout rollback",
                            extra={"reservation_id": reservation.reservation_id},
                        )
            for order in created_orders:
                for line in order.metadata.get("lines", []):
                    await self.products.apply_stock(
                        line["product_id"],
                        line["quantity"],
                        f"rollback:{checkout_id}:product:{line['product_id']}",
                    )
            raise

        checkout = Checkout(
            checkout_id,
            customer_id,
            total,
            "XOF",
            [o.id for o in created_orders],
            payment.get("payment_intent_id"),
            payment=payment,
            status=self._checkout_status_for_payment(payment),
            subtotal_minor=subtotal,
            delivery_fee_minor=delivery_total,
            discount_minor=discount_total,
            shop_breakdowns=breakdowns,
            payment_idempotency_key=idempotency_key,
        )
        await self.checkouts.save(checkout)
        for order in created_orders:
            order.metadata["payment_intent_id"] = checkout.payment_intent_id
            await self.orders.save(order)
            await append_outbox(self.outbox, new_outbox_message(
                "order.created", "order", order.id,
                {"order_id": order.id, "checkout_id": checkout.id, "shop_id": order.shop_id, "total_minor": order.total_minor, "currency": order.currency},
            ))
        return checkout

    async def get(self, checkout_id: str) -> Checkout:
        checkout = await self.checkouts.get(checkout_id)
        if checkout is None:
            raise ConflictError("checkout not found")
        payment_status = self._checkout_status_for_payment(checkout.payment or {})
        if checkout.status == CheckoutStatus.PAYMENT_PENDING and payment_status != CheckoutStatus.PAYMENT_PENDING:
            checkout.status = payment_status
            checkout.payment = {
                **(checkout.payment or {}),
                **self._payment_failure_fields(checkout.payment or {}),
            }
            await self.checkouts.save(checkout)
        return checkout

    async def _customer_phone_for_retry(self, checkout: Checkout) -> str:
        payment_phone = (checkout.payment or {}).get("customer_phone")
        if valid_customer_phone(payment_phone):
            return payment_phone
        for order_id in checkout.order_ids:
            order = await self.orders.get(order_id)
            if order is None:
                continue
            delivery_request = order.metadata.get("delivery_request") or {}
            phone = delivery_request.get("recipient_phone")
            if valid_customer_phone(phone):
                return phone
        return require_customer_phone(None)

    async def apply_payment_event(self, checkout_id: str, event_type: str, payload: dict) -> Checkout:
        checkout = await self.get(checkout_id)
        if event_type == "payment.succeeded":
            checkout.status = CheckoutStatus.PAYMENT_SUCCEEDED
        elif event_type == "payment.failed":
            checkout.status = CheckoutStatus.PAYMENT_FAILED
        else:
            return checkout
        checkout.payment = {**(checkout.payment or {}), **payload, "status": checkout.status.value}
        checkout.payment_intent_id = payload.get("payment_intent_id", checkout.payment_intent_id)
        await self.checkouts.save(checkout)
        return checkout

    async def retry_payment(
        self, checkout_id: str, idempotency_key: str, return_options: dict | None = None,
    ) -> Checkout:
        checkout = await self.get(checkout_id)
        if checkout.status != CheckoutStatus.PAYMENT_FAILED:
            raise ConflictError("only a failed checkout can retry payment")
        if checkout.payment_idempotency_key == idempotency_key:
            raise ConflictError("payment retry requires a new Idempotency-Key")
        customer_phone = await self._customer_phone_for_retry(checkout)
        previous_payment = checkout.payment or {}
        historical_returns = []
        for order_id in checkout.order_ids:
            order = await self.orders.get(order_id)
            if order is not None:
                historical_returns.append(order.metadata.get("delivery_request") or {})
        payment_return = self._payment_return(return_options or {}, previous_payment, *historical_returns)
        checkout.payment_attempt += 1
        checkout.status = CheckoutStatus.PAYMENT_PENDING
        checkout.payment_idempotency_key = idempotency_key
        checkout.payment = {
            **previous_payment, **payment_return.model_dump(), "customer_phone": customer_phone,
            "status": "pending", "failure_code": None, "failure_message": None,
            "payment_failure_code": None, "payment_failure_message": None,
        }
        await self.checkouts.save(checkout)

        payment = await self.payments.create_with_options(
            checkout.id,
            checkout.total_minor,
            idempotency_key,
            payment_method=previous_payment.get("payment_method", "wave"),
            **payment_return.model_dump(),
            customer_phone=customer_phone,
        )
        payment["payment_method"] = previous_payment.get("payment_method", "wave")
        payment["customer_phone"] = customer_phone
        payment.update(payment_return.model_dump())
        checkout.status = self._checkout_status_for_payment(payment)
        checkout.payment_intent_id = payment.get("payment_intent_id", checkout.payment_intent_id)
        checkout.payment = {**payment, **self._payment_failure_fields(payment)}
        await self.checkouts.save(checkout)
        return checkout
