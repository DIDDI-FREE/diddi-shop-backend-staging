from datetime import UTC, datetime, timedelta

import pytest

from app_base.core.api_contracts import cart_response, delivery_response, order_response
from app_base.core.errors import (
    ClaimWindowExpiredError,
    ConflictError,
    DeliveryAlreadyPickedUpError,
)
from app_base.modules.cart.application import CartService
from app_base.modules.cart.domain import CartLine
from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.domain import Product, ProductStatus
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.checkout.application.checkout_service import (
    CheckoutApplicationService,
    DeliveryQuotePort,
    PaymentIntentPort,
)
from app_base.modules.checkout.domain import CheckoutStatus
from app_base.modules.checkout.infra import InMemoryCheckoutRepository
from app_base.modules.claims.infra import InMemoryClaimRepository
from app_base.modules.delivery.domain import DeliveryProjection, DeliveryStatus
from app_base.modules.finance import FinanceService
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.infra import InMemoryShopRepository


@pytest.mark.asyncio
async def test_cart_response_contains_line_prices_and_shop_subtotals():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "Blue book", "", 2500, "XOF", 3, "books", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer-1")
    cart.lines = [CartLine("p1", "shop-1", 2)]
    await carts.save(cart)

    _, details, shop_totals = await CartService(carts, products).details("buyer-1")
    response = cart_response(cart, details, shop_totals)

    assert response["subtotal_minor"] == 5000
    assert response["lines"][0]["title"] == "Blue book"
    assert response["lines"][0]["line_total_minor"] == 5000
    assert response["shop_subtotals"] == [{"shop_id": "shop-1", "subtotal_minor": 5000}]


@pytest.mark.asyncio
async def test_cart_set_quantity_replaces_value_and_rejects_missing_line():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "Item", "", 1000, "XOF", 5, "books", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart_service = CartService(carts, products)
    await cart_service.add("buyer-1", "p1", 1)

    updated = await cart_service.set_quantity("buyer-1", "p1", 4)
    assert updated.lines[0].quantity == 4
    with pytest.raises(ConflictError, match="cart line not found"):
        await cart_service.set_quantity("buyer-1", "missing", 1)


class FixedQuote(DeliveryQuotePort):
    async def quote(self, shop_id, cart_lines, delivery_context=None):
        return 700


class RetryablePayment(PaymentIntentPort):
    def __init__(self):
        self.calls = []

    async def create(self, checkout_id, amount_minor, idempotency_key):
        self.calls.append((checkout_id, amount_minor, idempotency_key))
        return {
            "payment_intent_id": f"pi-{len(self.calls)}",
            "amount_minor": amount_minor,
            "currency": "XOF",
            "status": "pending",
        }


class FailedThenSuccessfulPayment(RetryablePayment):
    async def create(self, checkout_id, amount_minor, idempotency_key):
        self.calls.append((checkout_id, amount_minor, idempotency_key))
        if len(self.calls) == 1:
            return {
                "payment_intent_id": "pi-failed",
                "amount_minor": amount_minor,
                "currency": "XOF",
                "status": "failed",
                "failure_code": "provider_declined",
                "failure_message": "The provider declined the payment",
                "provider_status": "DECLINED",
            }
        return {
            "payment_intent_id": "pi-success",
            "amount_minor": amount_minor,
            "currency": "XOF",
            "status": "succeeded",
        }


@pytest.mark.asyncio
async def test_failed_payment_persists_failure_and_retry_reopens_payment():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "Item", "", 2500, "XOF", 2, "books", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer-1")
    cart.lines = [CartLine("p1", "shop-1", 1)]
    payments = FailedThenSuccessfulPayment()
    checkouts = InMemoryCheckoutRepository()
    service = CheckoutApplicationService(
        carts, products, checkouts, InMemoryOrderRepository(), FixedQuote(), payments, []
    )

    checkout = await service.create("buyer-1", "create-failed-1")
    assert checkout.status == CheckoutStatus.PAYMENT_FAILED
    assert checkout.payment["payment_failure_code"] == "provider_declined"
    assert checkout.payment["payment_failure_message"] == "The provider declined the payment"
    assert checkout.payment["payment_provider_status"] == "DECLINED"

    retried = await service.retry_payment(checkout.id, "retry-success-1")
    assert retried.status == CheckoutStatus.PAYMENT_SUCCEEDED
    assert retried.payment_intent_id == "pi-success"
    assert retried.payment_attempt == 2


@pytest.mark.asyncio
async def test_quote_and_payment_retry_have_stable_contracts():
    products = InMemoryProductRepository()
    await products.save(Product("p1", "shop-1", "Item", "", 2500, "XOF", 2, "books", [], ProductStatus.PUBLISHED))
    carts = InMemoryCartRepository()
    cart = await carts.get_or_create("buyer-1")
    cart.lines = [CartLine("p1", "shop-1", 1)]
    payments = RetryablePayment()
    checkouts = InMemoryCheckoutRepository()
    service = CheckoutApplicationService(
        carts, products, checkouts, InMemoryOrderRepository(), FixedQuote(), payments, []
    )

    quote = await service.quote("buyer-1", {"dropoff_location": {"lat": 3.8, "lng": 11.5}})
    assert quote["currency"] == "XOF"
    assert quote["subtotal_minor"] == 2500
    assert quote["delivery_fee_minor"] == 700
    assert quote["total_minor"] == 3200
    assert quote["shop_breakdowns"][0]["shop_id"] == "shop-1"

    checkout = await service.create("buyer-1", "create-1")
    await service.apply_payment_event(checkout.id, "payment.failed", {"payment_intent_id": "pi-1"})
    retried = await service.retry_payment(checkout.id, "retry-1")
    assert retried.status == CheckoutStatus.PAYMENT_PENDING
    assert retried.payment_attempt == 2
    assert payments.calls[-1][2] == "retry-1"

    await service.apply_payment_event(checkout.id, "payment.failed", {"payment_intent_id": "pi-2"})
    with pytest.raises(ConflictError, match="new Idempotency-Key"):
        await service.retry_payment(checkout.id, "retry-1")


@pytest.mark.asyncio
async def test_order_and_delivery_responses_expose_operational_fields():
    order = Order(
        "o1",
        "shop-1",
        "checkout-1",
        3200,
        fulfillment_status=FulfillmentStatus.TO_CONFIRM,
        metadata={
            "items_total": 2500,
            "delivery_fee": 700,
            "lines": [{"product_id": "p1", "title": "Item", "unit_price_minor": 2500, "quantity": 1}],
            "delivery_request": {"recipient_name": "Buyer", "dropoff_address": "Douala"},
        },
    )
    order_payload = order_response(order)
    assert order_payload["items"][0]["line_total_minor"] == 2500
    assert order_payload["created_at"]
    assert order_payload["seller_confirmation_deadline"]
    assert order_payload["recipient_name"] == "Buyer"

    delivery = DeliveryProjection(
        "d1", "o1", DeliveryStatus.IN_TRANSIT,
        courier={"name": "Courier"},
        dropoff_code="1234",
        position={"lat": 3.8, "lng": 11.5},
    )
    assert delivery_response(delivery, "o1")["dropoff_code"] == "1234"
    assert delivery_response(delivery, "o1")["position"]["latitude"] == 3.8


@pytest.mark.asyncio
async def test_product_statuses_and_photo_constraints_are_enforced():
    shops = InMemoryShopRepository()
    shop = await ShopService(shops).create("seller-1", "Shop", "Pickup", 3.8, 11.5)
    products = InMemoryProductRepository()

    class Files:
        async def metadata(self, file_id):
            return {"purpose": "diddishop_product_image", "status": "confirmed", "mime_type": "image/jpeg"}

        async def confirm_upload(self, file_id):
            return {"file_id": file_id}

    catalog = CatalogService(products, shops, Files())
    product = await catalog.create("seller-1", shop.id, "Item", "", 1000, 1, "books", [])
    await catalog.publish("seller-1", product.id)
    await catalog.pause("seller-1", product.id)
    await catalog.publish("seller-1", product.id)
    await catalog.retire("seller-1", product.id)
    with pytest.raises(ConflictError):
        await catalog.publish("seller-1", product.id)


@pytest.mark.asyncio
async def test_cancel_after_pickup_returns_stable_error_code():
    repo = InMemoryOrderRepository()
    await repo.create(Order("o1", "shop-1", "checkout-1", 1000, fulfillment_status=FulfillmentStatus.PICKED_UP))
    service = FinanceService(OrderService(repo, []), object(), object())

    with pytest.raises(DeliveryAlreadyPickedUpError) as exc_info:
        await service.cancel("o1", "buyer_requested")
    assert exc_info.value.code == "DELIVERY_ALREADY_PICKED_UP"


@pytest.mark.asyncio
async def test_claim_exposes_deadline_reason_code_and_evidence():
    repo = InMemoryOrderRepository()
    delivered_at = datetime.now(UTC) - timedelta(hours=1)
    order = Order("o-claim", "shop-1", "checkout-1", 1000, fulfillment_status=FulfillmentStatus.DELIVERED)
    order.metadata["delivered_at"] = delivered_at
    await repo.create(order)
    claims = InMemoryClaimRepository()
    service = FinanceService(OrderService(repo, []), claims, object(), claim_window_hours=72)

    claim = await service.open_claim(
        "o-claim",
        "buyer-1",
        "article endommage",
        reason_code="damaged",
        evidence_file_ids=["file-1"],
    )
    assert claim.reason_code == "damaged"
    assert claim.evidence_file_ids == ["file-1"]
    assert claim.claim_deadline == delivered_at + timedelta(hours=72)

    expired = Order("o-expired", "shop-1", "checkout-2", 1000, fulfillment_status=FulfillmentStatus.DELIVERED)
    expired.metadata["delivered_at"] = datetime.now(UTC) - timedelta(hours=73)
    await repo.create(expired)
    with pytest.raises(ClaimWindowExpiredError) as exc_info:
        await service.open_claim("o-expired", "buyer-1", "too late")
    assert exc_info.value.code == "CLAIM_WINDOW_EXPIRED"
