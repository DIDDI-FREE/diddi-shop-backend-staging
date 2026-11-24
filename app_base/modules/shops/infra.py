from app_base.modules.shops.domain import Shop


class InMemoryShopRepository:
    def __init__(self):
        self.items: dict[str, Shop] = {}

    async def save(self, shop: Shop) -> None:
        self.items[shop.id] = shop

    async def get(self, shop_id: str) -> Shop | None:
        return self.items.get(shop_id)

    async def list_for_owner(self, owner_id: str) -> list[Shop]:
        return [shop for shop in self.items.values() if shop.owner_id == owner_id]
