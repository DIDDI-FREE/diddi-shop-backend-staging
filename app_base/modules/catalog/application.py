from uuid import uuid4

from app_base.core.errors import ConflictError, NotFoundError
from app_base.modules.catalog.domain import (
    ALLOWED_PRODUCT_IMAGE_MIME_TYPES,
    MAX_PRODUCT_PHOTOS,
    Product,
    ProductRepository,
    ProductStatus,
)
from app_base.modules.shops.domain import ShopRepository, ShopStatus
from app_base.shared_kernel.money import ceil_xof


class CatalogService:
    def __init__(self, repository: ProductRepository, shops: ShopRepository, files=None):
        self.repository = repository
        self.shops = shops
        self.files = files

    async def create(self, owner_id: str, shop_id: str, title: str, description: str, price_minor: int, stock: int, category: str, photo_file_ids: list[str]) -> Product:
        price_minor = ceil_xof(price_minor)
        shop = await self.shops.get(shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("shop ownership invalid")
        if shop.status != ShopStatus.ACTIVE:
            raise ConflictError("suspended shop cannot publish products")
        if price_minor < 0 or stock < 0:
            raise ValueError("price and stock must be non-negative")
        if len(photo_file_ids) > MAX_PRODUCT_PHOTOS:
            raise ConflictError(f"a product cannot have more than {MAX_PRODUCT_PHOTOS} photos")
        if self.files is not None:
            for file_id in photo_file_ids:
                metadata = await self.files.metadata(file_id)
                if metadata.get("purpose") != "diddishop_product_image":
                    raise ConflictError("file purpose is not a DiddiShop product image")
                if metadata.get("mime_type") and metadata["mime_type"] not in ALLOWED_PRODUCT_IMAGE_MIME_TYPES:
                    raise ConflictError("unsupported product image format")
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
        if product.status not in {ProductStatus.DRAFT, ProductStatus.PAUSED}:
            raise ConflictError("only draft or paused products can be published")
        product.status = ProductStatus.PUBLISHED
        await self.repository.save(product)
        return product

    async def pause(self, owner_id: str, product_id: str) -> Product:
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        if product.status != ProductStatus.PUBLISHED:
            raise ConflictError("only published products can be paused")
        product.status = ProductStatus.PAUSED
        await self.repository.save(product)
        return product

    async def retire(self, owner_id: str, product_id: str) -> Product:
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        if product.status == ProductStatus.RETIRED:
            return product
        product.status = ProductStatus.RETIRED
        await self.repository.save(product)
        return product

    async def get(self, product_id: str) -> Product:
        product = await self.repository.get(product_id)
        if product is None:
            raise NotFoundError("product not found")
        return product

    async def list_published(
        self,
        *,
        shop_id: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[Product]:
        return await self.repository.list_published(shop_id, category, search)

    async def list_for_shop(self, shop_id: str, owner_id: str | None = None) -> list[Product]:
        if owner_id is not None:
            shop = await self.shops.get(shop_id)
            if shop is None or shop.owner_id != owner_id:
                raise ConflictError("shop ownership invalid")
        return await self.repository.list_for_shop(shop_id)

    async def list_for_owner(self, owner_id: str, shop_id: str | None = None) -> list[Product]:
        shops = [await self.shops.get(shop_id)] if shop_id else await self.shops.list_for_owner(owner_id)
        if shop_id and (shops[0] is None or shops[0].owner_id != owner_id):
            raise ConflictError("shop ownership invalid")
        products: list[Product] = []
        for shop in shops:
            if shop is not None:
                products.extend(await self.repository.list_for_shop(shop.id))
        return products

    async def update(
        self,
        owner_id: str,
        product_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        price_minor: int | None = None,
        stock: int | None = None,
        category: str | None = None,
    ) -> Product:
        if price_minor is not None:
            price_minor = ceil_xof(price_minor)
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        if price_minor is not None and price_minor < 0:
            raise ValueError("price must be non-negative")
        if stock is not None and stock < 0:
            raise ValueError("stock must be non-negative")
        for field, value in {
            "title": title,
            "description": description,
            "price_minor": price_minor,
            "stock": stock,
            "category": category,
        }.items():
            if value is not None:
                setattr(product, field, value)
        await self.repository.save(product)
        return product

    async def add_photo(self, owner_id: str, product_id: str, file_id: str) -> Product:
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        if self.files is None:
            raise ConflictError("DiddiFiles is not configured")
        if len(product.photo_file_ids) >= MAX_PRODUCT_PHOTOS and file_id not in product.photo_file_ids:
            raise ConflictError(f"a product cannot have more than {MAX_PRODUCT_PHOTOS} photos")
        await self.files.confirm_upload(file_id)
        metadata = await self.files.metadata(file_id)
        if metadata.get("purpose") != "diddishop_product_image":
            raise ConflictError("file purpose is not a DiddiShop product image")
        if metadata.get("mime_type") and metadata["mime_type"] not in ALLOWED_PRODUCT_IMAGE_MIME_TYPES:
            raise ConflictError("unsupported product image format")
        if metadata.get("status") not in {None, "confirmed", "ready", "available"}:
            raise ConflictError("product image is not confirmed")
        if file_id not in product.photo_file_ids:
            product.photo_file_ids.append(file_id)
            await self.repository.save(product)
        return product

    async def create_photo_upload_session(
        self,
        owner_id: str,
        product_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> dict:
        product = await self.get(product_id)
        shop = await self.shops.get(product.shop_id)
        if shop is None or shop.owner_id != owner_id:
            raise ConflictError("product ownership invalid")
        if self.files is None:
            raise ConflictError("DiddiFiles is not configured")
        return await self.files.create_upload_session({
            "filename": filename,
            "mime_type": content_type,
            "size_bytes": size_bytes,
            "module_owner": "diddishop",
            "purpose": "diddishop_product_image",
            "metadata": {"product_id": product_id},
        })

    async def photo_urls(self, product: Product) -> list[str]:
        if self.files is None:
            return []
        return [await self.files.public_or_signed_url(file_id) for file_id in product.photo_file_ids]

    async def decrement(self, product_id: str, quantity: int, operation_id: str) -> Product:
        return await self.repository.apply_stock(product_id, -quantity, operation_id)

    async def restore(self, product_id: str, quantity: int, operation_id: str) -> Product:
        return await self.repository.apply_stock(product_id, quantity, operation_id)
