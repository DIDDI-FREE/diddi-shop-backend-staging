from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class CartLine:
    product_id: str
    shop_id: str
    quantity: int


@dataclass
class Cart:
    id: str
    customer_id: str
    lines: list[CartLine] = field(default_factory=list)


class CartRepository(Protocol):
    async def get_or_create(self, customer_id: str) -> Cart: ...
    async def save(self, cart: Cart) -> None: ...
