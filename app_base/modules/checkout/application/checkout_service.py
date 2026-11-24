from dataclasses import dataclass
from uuid import uuid4

from app_base.core.errors import ConflictError
from app_base.core.outbox import OutboxMessage, append_outbox, new_outbox_message
from app_base.modules.cart.domain import CartRepository
from app_base.modules.catalog.domain import ProductRepository
from app_base.modules.checkout.domain import Checkout, CheckoutRepository
from app_base.modules.orders.domain.entities import Order
from app_base.modules.orders.domain.interfaces import OrderRepository


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

    async def create(self, customer_id: str, idempotency_key: str) -> Checkout:
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
        total = 0
        try:
            for shop_id, lines in grouped.items():
                items_total = sum(item["product"].price_minor * item["quantity"] for item in lines)
                delivery_fee = await self.delivery_quotes.quote(shop_id, lines)
                order_id = str(uuid4())
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
                    total_minor=items_total + delivery_fee,
                    currency="XAF",
                    metadata={
                        "items_total": items_total,
                        "delivery_fee": delivery_fee,
                        "lines": [
                            {
                                "product_id": item["product"].id,
                                "title": item["product"].title,
                                "unit_price_minor": item["product"].price_minor,
                                "quantity": item["quantity"],
                            }
                            for item in lines
                        ],
                    },
                )
                await self.orders.create(order)
                created_orders.append(order)
                total += order.total_minor
            payment = await self.payments.create(checkout_id, total, idempotency_key)
        except Exception:
            for order in created_orders:
                for line in order.metadata.get("lines", []):
                    await self.products.apply_stock(
                        line["product_id"],
                        line["quantity"],
                        f"rollback:{checkout_id}:product:{line['product_id']}",
                    )
            raise

        checkout = Checkout(checkout_id, customer_id, total, "XAF", [o.id for o in created_orders], payment.get("payment_intent_id"))
        await self.checkouts.save(checkout)
        for order in created_orders:
            order.metadata["payment_intent_id"] = checkout.payment_intent_id
            await self.orders.save(order)
            await append_outbox(self.outbox, new_outbox_message(
                "order.created", "order", order.id,
                {"order_id": order.id, "checkout_id": checkout.id, "shop_id": order.shop_id, "total_minor": order.total_minor, "currency": order.currency},
            ))
        return checkout
