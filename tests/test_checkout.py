import pytest

from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.domain import Product, ProductStatus
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.checkout.application.checkout_service import (
    CheckoutApplicationService,
    DeliveryQuotePort,
    PaymentIntentPort,
)
from app_base.modules.checkout.infra import InMemoryCheckoutRepository
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


class Quote(DeliveryQuotePort):
    async def quote(self, shop_id, cart_lines):
        return 500


class Payment(PaymentIntentPort):
    async def create(self, checkout_id, amount_minor, idempotency_key):
        return {"payment_intent_id": f"pi-{checkout_id}", "amount_minor": amount_minor}


@pytest.mark.asyncio
async def test_checkout_creates_one_order_per_shop_and_snapshots_price():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "A", "", 1000, "XAF", 2, "x", [], ProductStatus.PUBLISHED))
    await products.save(Product("p2", "shop-2", "B", "", 2000, "XAF", 2, "x", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer")
    from app_base.modules.cart.domain import CartLine
    cart.lines = [CartLine("p1", "shop-1", 1), CartLine("p2", "shop-2", 1)]
    service = CheckoutApplicationService(
        carts, products, InMemoryCheckoutRepository(), InMemoryOrderRepository(), Quote(), Payment(), []
    )
    checkout = await service.create("buyer", "shop:checkout:1")
    assert len(checkout.order_ids) == 2
    assert checkout.total_minor == 4000
    assert products.items["p1"].stock == 1
    assert products.items["p2"].stock == 1
    for order_id in checkout.order_ids:
        order = await service.orders.get(order_id)
        assert order.metadata["payment_intent_id"] == "pi-" + checkout.id
