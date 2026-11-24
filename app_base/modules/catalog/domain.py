from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app_base.shared_kernel.currency import require_xof


class ProductStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    RETIRED = "retired"


@dataclass
class Product:
    id: str
    shop_id: str
    title: str
    description: str
    price_minor: int
    currency: str
    stock: int
    category: str
    photo_file_ids: list[str]
    status: ProductStatus = ProductStatus.DRAFT

    def __post_init__(self) -> None:
        require_xof(self.currency)


class ProductRepository(Protocol):
    async def save(self, product: Product) -> None: ...
    async def get(self, product_id: str) -> Product | None: ...
    async def list_published(self, shop_id: str | None = None) -> list[Product]: ...
    async def apply_stock(self, product_id: str, delta: int, operation_id: str) -> Product: ...
