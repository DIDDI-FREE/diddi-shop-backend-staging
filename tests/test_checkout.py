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
from app_base.modules.rewards.application import RewardsService
from app_base.shared_kernel.contracts.rewards import RewardReservation


class Quote(DeliveryQuotePort):
    async def quote(self, shop_id, cart_lines, delivery_context=None):
        return 500


class Payment(PaymentIntentPort):
    def __init__(self):
        self.amounts = []

    async def create(self, checkout_id, amount_minor, idempotency_key):
        self.amounts.append(amount_minor)
        return {"payment_intent_id": f"pi-{checkout_id}", "amount_minor": amount_minor}

    async def create_with_options(self, checkout_id, amount_minor, idempotency_key, **options):
        assert options["customer_phone"] == "+2250700000000"
        return await self.create(checkout_id, amount_minor, idempotency_key)


@pytest.mark.asyncio
async def test_checkout_creates_one_order_per_shop_and_snapshots_price():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "A", "", 1000, "XOF", 2, "x", [], ProductStatus.PUBLISHED))
    await products.save(Product("p2", "shop-2", "B", "", 2000, "XOF", 2, "x", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer")
    from app_base.modules.cart.domain import CartLine
    cart.lines = [CartLine("p1", "shop-1", 1), CartLine("p2", "shop-2", 1)]
    service = CheckoutApplicationService(
        carts, products, InMemoryCheckoutRepository(), InMemoryOrderRepository(), Quote(), Payment(), []
    )
    checkout = await service.create("buyer", "shop:checkout:1", {"recipient_phone": "+2250700000000"})
    assert len(checkout.order_ids) == 2
    assert checkout.total_minor == 4000
    assert products.items["p1"].stock == 1
    assert products.items["p2"].stock == 1
    for order_id in checkout.order_ids:
        order = await service.orders.get(order_id)
        assert order.metadata["payment_intent_id"] == "pi-" + checkout.id


@pytest.mark.asyncio
async def test_checkout_applies_xof_rewards_before_payment():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "A", "", 1000, "XOF", 2, "x", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer")
    from app_base.modules.cart.domain import CartLine
    cart.lines = [CartLine("p1", "shop-1", 1)]

    class Adapter:
        async def quote(self, _payload):
            from app_base.shared_kernel.contracts.rewards import RewardQuote
            return RewardQuote(
                eligible=True,
                entitlement_id="ent-1",
                campaign_version_id="version-1",
                discount_minor=100,
                final_amount_minor=1400,
                currency="XOF",
            )

        async def reserve(self, payload, idempotency_key):
            return RewardReservation(
                reservation_id="res-1",
                entitlement_id=payload["entitlement_id"],
                operation_id=idempotency_key,
                reserved_amount_minor=100,
            )

    payment = Payment()
    service = CheckoutApplicationService(
        carts,
        products,
        InMemoryCheckoutRepository(),
        InMemoryOrderRepository(),
        Quote(),
        payment,
        [],
        rewards=RewardsService(Adapter()),
    )
    checkout = await service.create(
        "buyer",
        "shop:checkout:rewards:1",
        {"rewards_campaign_id": "campaign-1", "recipient_phone": "+2250700000000"},
    )

    assert checkout.currency == "XOF"
    assert checkout.total_minor == 1400
    assert payment.amounts == [1400]
    order = await service.orders.get(checkout.order_ids[0])
    assert order.metadata["rewards_discount_minor"] == 100
    assert order.metadata["rewards"]["snapshot"]["currency"] == "XOF"
