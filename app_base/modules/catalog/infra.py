from app_base.core.errors import ConflictError, DiddiShopError
from app_base.modules.catalog.domain import Product


class InMemoryProductRepository:
    def __init__(self):
        self.items: dict[str, Product] = {}
        self.operations: set[str] = set()

    async def save(self, product: Product) -> None:
        self.items[product.id] = product

    async def get(self, product_id: str) -> Product | None:
        return self.items.get(product_id)

    async def list_published(
        self,
        shop_id: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[Product]:
        needle = search.casefold().strip() if search else None
        return [
            p for p in self.items.values()
            if p.status.value == "published"
            and (shop_id is None or p.shop_id == shop_id)
            and (category is None or p.category == category)
            and (needle is None or needle in f"{p.title} {p.description}".casefold())
        ]

    async def list_for_shop(self, shop_id: str) -> list[Product]:
        return [p for p in self.items.values() if p.shop_id == shop_id]

    async def apply_stock(self, product_id: str, delta: int, operation_id: str) -> Product:
        product = await self.get(product_id)
        if product is None:
            raise DiddiShopError("product not found")
        if operation_id in self.operations:
            return product
        if product.stock + delta < 0:
            raise ConflictError("insufficient stock")
        product.stock += delta
        self.operations.add(operation_id)
        return product
