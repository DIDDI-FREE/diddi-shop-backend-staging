from uuid import uuid4

from app_base.core.errors import ConflictError, DiddiShopError
from app_base.modules.catalog.domain import Product, ProductRepository, ProductStatus
from app_base.modules.shops.domain import ShopRepository, ShopStatus


class CatalogService:
    def __init__(self, repository: ProductRepository, shops: ShopRepository, files=None):
        self.repository = repository
        self.shops = shops
        self.files = files

    async def create(self, owner_id: str, shop_id: str, title: str, description: str, price_minor: int, stock: int, category: str, photo_file_ids: list[str]) -> Product:
        shop = await self.shops.get(shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("shop ownership invalid")
        if shop.status != ShopStatus.ACTIVE:
            raise ConflictError("suspended shop cannot publish products")
        if price_minor < 0 or stock < 0:
            raise ValueError("price and stock must be non-negative")
        if self.files is not None:
            for file_id in photo_file_ids:
                metadata = await self.files.metadata(file_id)
                if metadata.get("purpose") != "diddishop_product_image":
                    raise ConflictError("file purpose is not a DiddiShop product image")
                if metadata.get("status") not in {None, "confirmed", "ready", "available"}:
                    raise ConflictError("product image is not confirmed")
        product = Product(str(uuid4()), shop_id, title, description, price_minor, "XOF", stock, category, photo_file_ids)
        await self.repository.save(product)
        return product

    async def publish(self, owner_id: str, product_id: str) -> Product:
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        product.status = ProductStatus.PUBLISHED
        await self.repository.save(product)
        return product

    async def get(self, product_id: str) -> Product:
        product = await self.repository.get(product_id)
        if product is None:
            raise DiddiShopError("product not found")
        return product

    async def decrement(self, product_id: str, quantity: int, operation_id: str) -> Product:
        return await self.repository.apply_stock(product_id, -quantity, operation_id)

    async def restore(self, product_id: str, quantity: int, operation_id: str) -> Product:
        return await self.repository.apply_stock(product_id, quantity, operation_id)
