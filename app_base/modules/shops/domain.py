from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ShopStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass
class Shop:
    id: str
    owner_id: str
    name: str
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    status: ShopStatus = ShopStatus.ACTIVE


class ShopRepository(Protocol):
    async def save(self, shop: Shop) -> None: ...
    async def get(self, shop_id: str) -> Shop | None: ...
    async def list_for_owner(self, owner_id: str) -> list[Shop]: ...
