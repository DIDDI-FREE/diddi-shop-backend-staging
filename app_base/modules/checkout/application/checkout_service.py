import logging
from dataclasses import dataclass
from uuid import uuid4

from app_base.core.errors import ConflictError
from app_base.core.outbox import OutboxMessage, append_outbox, new_outbox_message
from app_base.modules.cart.domain import CartRepository
from app_base.modules.catalog.domain import ProductRepository
from app_base.modules.checkout.domain import Checkout, CheckoutRepository
from app_base.modules.orders.domain.entities import Order
from app_base.modules.orders.domain.interfaces import OrderRepository
from app_base.modules.rewards.application import RewardsService
from app_base.modules.shops.domain import ShopRepository

logger = logging.getLogger(__name__)


class DeliveryQuotePort:
    async def quote(self, shop_id: str, cart_lines: list[dict]) -> int:
        raise NotImplementedError


class PaymentIntentPort:
    async def create(self, checkout_id: str, amount_minor: int, idempotency_key: str) -> dict:
        raise NotImplementedError


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

    async def create(self, customer_id: str, idempotency_key: str, delivery_context: dict | None = None) -> Checkout:
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
                "quantity": line.quantity,
            })

        checkout_id = str(uuid4())
        created_orders: list[Order] = []
        reward_reservations = []
        total = 0
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
                            }
                            for item in lines
                        ],
                        "delivery_request": {
                            **quote_context,
                            "customer_user_id": customer_id,
                            "recipient_user_id": customer_id,
                            "sender_user_id": shop.owner_id if shop is not None else "diddishop-system",
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
                        },
                    },
                )
                await self.orders.create(order)
                created_orders.append(order)
                total += order.total_minor
            payment = await self.payments.create(checkout_id, total, idempotency_key)
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
