import pytest

from app_base.core.api_contracts import checkout_response, product_response
from app_base.modules.cart.application import CartService
from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.checkout.domain import Checkout
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.infra import InMemoryShopRepository


@pytest.mark.asyncio
async def test_frontend_catalog_search_update_and_photo_contract():
    shops = InMemoryShopRepository()
    products = InMemoryProductRepository()
    shop = await ShopService(shops).create("seller-1", "Shop", "Pickup", 3.8, 11.5)

    class Files:
        async def metadata(self, file_id):
            return {"id": file_id, "purpose": "diddishop_product_image", "status": "confirmed"}

        async def create_upload_session(self, payload):
            return {"file_id": "file-1", "upload": payload}

    catalog = CatalogService(products, shops, Files())
    product = await catalog.create("seller-1", shop.id, "Blue Book", "Novel", 2500, 3, "books", [])
    await catalog.publish("seller-1", product.id)

    listed = await catalog.list_published(category="books", search="blue")
    assert [item.id for item in listed] == [product.id]
    updated = await catalog.update("seller-1", product.id, price_minor=3000, stock=5)
    assert product_response(updated)["price_minor"] == 3000
    await catalog.add_photo("seller-1", product.id, "file-1")
    assert product_response(updated)["photo_file_ids"] == ["file-1"]

    session = await catalog.create_photo_upload_session("seller-1", product.id, "book.jpg", "image/jpeg", 100)
    assert session["upload"]["purpose"] == "diddishop_product_image"


@pytest.mark.asyncio
async def test_frontend_cart_remove_and_seller_order_listing_contract():
    shops = InMemoryShopRepository()
    products = InMemoryProductRepository()
    shop = await ShopService(shops).create("seller-1", "Shop", "Pickup", 3.8, 11.5)
    from app_base.modules.catalog.domain import Product, ProductStatus

    product = Product("p1", shop.id, "Item", "", 100, "XOF", 2, "misc", [], ProductStatus.PUBLISHED)
    await products.save(product)
    cart = CartService(InMemoryCartRepository(), products)
    await cart.add("buyer-1", product.id, 1)
    assert (await cart.remove("buyer-1", product.id)).lines == []

    orders = InMemoryOrderRepository()
    await orders.create(Order("o1", shop.id, "c1", 100, fulfillment_status=FulfillmentStatus.TO_CONFIRM))
    assert [order.id for order in await orders.list_for_shop(shop.id)] == ["o1"]


def test_checkout_response_exposes_normalized_payment_without_secrets():
    checkout = Checkout(
        "c1",
        "buyer-1",
        3500,
        "XOF",
        ["o1"],
        "pi-1",
        payment={"payment_intent_id": "pi-1", "amount_minor": 3500, "currency": "XOF", "status": "created", "token": "must-not-leak"},
    )
    response = checkout_response(checkout, checkout.payment)
    assert response["payment"] == {
        "payment_intent_id": "pi-1",
        "amount_minor": 3500,
        "currency": "XOF",
        "status": "created",
    }
