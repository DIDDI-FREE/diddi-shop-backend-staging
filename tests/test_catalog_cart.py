import pytest

from app_base.core.errors import ConflictError
from app_base.modules.cart.application import CartService
from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.infra import InMemoryShopRepository


@pytest.mark.asyncio
async def test_product_publication_and_cart_grouping():
    shops = InMemoryShopRepository()
    products = InMemoryProductRepository()
    shop_service = ShopService(shops)
    shop = await shop_service.create("seller-1", "Shop One", "Pickup", 3.86, 11.52)
    catalog = CatalogService(products, shops)
    product = await catalog.create("seller-1", shop.id, "Book", "", 2500, 2, "books", [])
    await catalog.publish("seller-1", product.id)
    cart = CartService(InMemoryCartRepository(), products)
    current = await cart.add("buyer-1", product.id, 1)
    assert current.lines[0].shop_id == shop.id
    assert current.lines[0].quantity == 1


@pytest.mark.asyncio
async def test_stock_decrement_and_restore_are_idempotent():
    repo = InMemoryProductRepository()
    from app_base.modules.catalog.domain import Product, ProductStatus
    product = Product("p1", "s1", "Item", "", 100, "XOF", 1, "misc", [], ProductStatus.PUBLISHED)
    await repo.save(product)
    await repo.apply_stock("p1", -1, "checkout:1:p1")
    await repo.apply_stock("p1", -1, "checkout:1:p1")
    assert product.stock == 0
    await repo.apply_stock("p1", 1, "cancel:1:p1")
    await repo.apply_stock("p1", 1, "cancel:1:p1")
    assert product.stock == 1


@pytest.mark.asyncio
async def test_catalog_rejects_non_product_file_purpose():
    shops = InMemoryShopRepository()
    shop_service = ShopService(shops)
    shop = await shop_service.create("owner-1", "Shop", "Address", 3.8, 11.5)

    class Files:
        async def confirm_upload(self, _file_id):
            return {"status": "confirmed"}

        async def metadata(self, _file_id):
            return {"purpose": "generic_private_document", "status": "confirmed"}

    with pytest.raises(ConflictError):
        await CatalogService(InMemoryProductRepository(), shops, Files()).create(
            "owner-1", shop.id, "Item", "", 100, 1, "cat", ["file-1"]
        )
