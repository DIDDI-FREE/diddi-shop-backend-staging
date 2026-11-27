from uuid import uuid4

from app_base.core.errors import ConflictError, NotFoundError
from app_base.modules.shops.domain import Shop, ShopRepository, ShopStatus


class ShopService:
    def __init__(self, repository: ShopRepository):
        self.repository = repository

    async def create(self, owner_id: str, name: str, pickup_address: str, latitude: float, longitude: float) -> Shop:
        shop = Shop(str(uuid4()), owner_id, name, pickup_address, latitude, longitude)
        await self.repository.save(shop)
        return shop

    async def get_owned(self, shop_id: str, owner_id: str) -> Shop:
        shop = await self.repository.get(shop_id)
        if shop is None:
            raise NotFoundError("shop not found")
        if shop.owner_id != owner_id:
            raise ConflictError("shop does not belong to actor")
        return shop

    async def get(self, shop_id: str) -> Shop:
        shop = await self.repository.get(shop_id)
        if shop is None:
            raise NotFoundError("shop not found")
        return shop

    async def get_public(self, shop_id: str) -> Shop:
        return await self.get(shop_id)

    async def list_for_owner(self, owner_id: str) -> list[Shop]:
        return await self.repository.list_for_owner(owner_id)

    async def set_status(self, shop_id: str, owner_id: str, status: ShopStatus) -> Shop:
        shop = await self.get_owned(shop_id, owner_id)
        shop.status = status
        await self.repository.save(shop)
        return shop
