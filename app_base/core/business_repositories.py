import json
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_base.core.business_models import (
    CartRecord,
    CheckoutRecord,
    ClaimRecord,
    DeliveryRecord,
    OrderRecord,
    ProductRecord,
    ShopRecord,
    StockOperationRecord,
)
from app_base.core.errors import ConflictError, DiddiShopError
from app_base.modules.cart.domain import Cart, CartLine
from app_base.modules.catalog.domain import Product, ProductStatus
from app_base.modules.checkout.domain import Checkout
from app_base.modules.claims.domain import Claim
from app_base.modules.delivery.domain import DeliveryProjection
from app_base.modules.orders.domain.entities import Order
from app_base.modules.shops.domain import Shop


def _dump(value) -> str:
    return json.dumps(asdict(value), separators=(",", ":"), default=lambda item: item.value if hasattr(item, "value") else str(item))


def _load(payload: str) -> dict:
    return json.loads(payload)


def _cart(payload: str) -> Cart:
    data = _load(payload)
    data["lines"] = [CartLine(**line) for line in data.get("lines", [])]
    return Cart(**data)


def _product(payload: str) -> Product:
    data = _load(payload)
    # JSON persistence stores StrEnum values as strings. Rehydrate the domain
    # enum before application services access ProductStatus.value.
    data["status"] = ProductStatus(data["status"])
    return Product(**data)


class SqlShopRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def save(self, shop: Shop) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(ShopRecord, shop.id)
            values = {"owner_id": shop.owner_id, "status": shop.status.value, "payload": _dump(shop)}
            if row is None:
                session.add(ShopRecord(id=shop.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    async def get(self, shop_id: str) -> Shop | None:
        async with self.factory() as session:
            row = await session.get(ShopRecord, shop_id)
            return Shop(**_load(row.payload)) if row else None

    async def list_for_owner(self, owner_id: str) -> list[Shop]:
        async with self.factory() as session:
            result = await session.execute(select(ShopRecord).where(ShopRecord.owner_id == owner_id))
            return [Shop(**_load(row.payload)) for row in result.scalars()]


class SqlProductRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def save(self, product: Product) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(ProductRecord, product.id)
            values = {"shop_id": product.shop_id, "status": product.status.value, "stock": product.stock, "payload": _dump(product)}
            if row is None:
                session.add(ProductRecord(id=product.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    async def get(self, product_id: str) -> Product | None:
        async with self.factory() as session:
            row = await session.get(ProductRecord, product_id)
            return _product(row.payload) if row else None

    async def list_published(
        self,
        shop_id: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[Product]:
        async with self.factory() as session:
            query = select(ProductRecord).where(ProductRecord.status == "published")
            if shop_id is not None:
                query = query.where(ProductRecord.shop_id == shop_id)
            result = await session.execute(query)
            products = [_product(row.payload) for row in result.scalars()]
            needle = search.casefold().strip() if search else None
            return [
                product for product in products
                if (category is None or product.category == category)
                and (needle is None or needle in f"{product.title} {product.description}".casefold())
            ]

    async def list_for_shop(self, shop_id: str) -> list[Product]:
        async with self.factory() as session:
            result = await session.execute(select(ProductRecord).where(ProductRecord.shop_id == shop_id))
            return [_product(row.payload) for row in result.scalars()]

    async def apply_stock(self, product_id: str, delta: int, operation_id: str) -> Product:
        async with self.factory() as session, session.begin():
            operation = await session.get(StockOperationRecord, operation_id)
            row = await session.get(ProductRecord, product_id, with_for_update=True)
            if row is None:
                raise DiddiShopError("product not found")
            if operation is None:
                if row.stock + delta < 0:
                    raise ConflictError("insufficient stock")
                row.stock += delta
                payload = _load(row.payload)
                payload["stock"] = row.stock
                row.payload = json.dumps(payload, separators=(",", ":"))
                session.add(StockOperationRecord(operation_id=operation_id, product_id=product_id))
            return _product(row.payload)


class SqlCartRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def get_or_create(self, customer_id: str) -> Cart:
        async with self.factory() as session, session.begin():
            result = await session.execute(select(CartRecord).where(CartRecord.customer_id == customer_id))
            row = result.scalar_one_or_none()
            if row is None:
                cart = Cart.create(customer_id)
                row = CartRecord(id=cart.id, customer_id=customer_id, payload=_dump(cart))
                session.add(row)
                return cart
            return _cart(row.payload)

    async def save(self, cart: Cart) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(CartRecord, cart.id)
            if row is None:
                session.add(CartRecord(id=cart.id, customer_id=cart.customer_id, payload=_dump(cart)))
            else:
                row.payload = _dump(cart)


class SqlCheckoutRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def save(self, checkout: Checkout) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(CheckoutRecord, checkout.id)
            values = {"customer_id": checkout.customer_id, "payload": _dump(checkout)}
            if row is None:
                session.add(CheckoutRecord(id=checkout.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    async def get(self, checkout_id: str) -> Checkout | None:
        async with self.factory() as session:
            row = await session.get(CheckoutRecord, checkout_id)
            return Checkout(**_load(row.payload)) if row else None

    async def list_for_customer(self, customer_id: str) -> list[Checkout]:
        async with self.factory() as session:
            result = await session.execute(select(CheckoutRecord).where(CheckoutRecord.customer_id == customer_id))
            return [Checkout(**_load(row.payload)) for row in result.scalars()]


class SqlOrderRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def get(self, order_id: str) -> Order | None:
        async with self.factory() as session:
            row = await session.get(OrderRecord, order_id)
            return Order(**_load(row.payload)) if row else None

    async def create(self, order: Order) -> None:
        async with self.factory() as session, session.begin():
            if await session.get(OrderRecord, order.id):
                raise ValueError(f"order {order.id} already exists")
            session.add(OrderRecord(
                id=order.id,
                shop_id=order.shop_id,
                checkout_id=order.checkout_id,
                fulfillment_status=order.fulfillment_status.value,
                payment_status=order.payment_status.value,
                version=order.version,
                payload=_dump(order),
            ))

    async def save(self, order: Order) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(OrderRecord, order.id, with_for_update=True)
            if row is None:
                raise DiddiShopError(f"Order {order.id} not found")
            if row.version > order.version:
                raise ConflictError("order version conflict")
            row.fulfillment_status = order.fulfillment_status.value
            row.payment_status = order.payment_status.value
            row.version = order.version
            row.payload = _dump(order)

    async def list_for_shop(self, shop_id: str) -> list[Order]:
        async with self.factory() as session:
            result = await session.execute(select(OrderRecord).where(OrderRecord.shop_id == shop_id))
            return [Order(**_load(row.payload)) for row in result.scalars()]


class SqlClaimRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def save(self, claim: Claim) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(ClaimRecord, claim.id)
            values = {"order_id": claim.order_id, "status": claim.status.value, "opened_at": claim.opened_at, "payload": _dump(claim)}
            if row is None:
                session.add(ClaimRecord(id=claim.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    async def get(self, claim_id: str) -> Claim | None:
        async with self.factory() as session:
            row = await session.get(ClaimRecord, claim_id)
            return Claim(**_load(row.payload)) if row else None

    async def get_open_for_order(self, order_id: str) -> Claim | None:
        async with self.factory() as session:
            result = await session.execute(select(ClaimRecord).where(ClaimRecord.order_id == order_id, ClaimRecord.status == "open"))
            row = result.scalar_one_or_none()
            return Claim(**_load(row.payload)) if row else None

    async def get_for_order(self, order_id: str) -> Claim | None:
        async with self.factory() as session:
            result = await session.execute(
                select(ClaimRecord).where(ClaimRecord.order_id == order_id).order_by(ClaimRecord.opened_at.desc())
            )
            row = result.scalars().first()
            return Claim(**_load(row.payload)) if row else None


class SqlDeliveryRepository:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def save(self, delivery: DeliveryProjection) -> None:
        async with self.factory() as session, session.begin():
            row = await session.get(DeliveryRecord, delivery.id)
            values = {"order_id": delivery.order_id, "status": delivery.status.value, "payload": _dump(delivery)}
            if row is None:
                session.add(DeliveryRecord(id=delivery.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    async def get_by_order(self, order_id: str) -> DeliveryProjection | None:
        async with self.factory() as session:
            result = await session.execute(select(DeliveryRecord).where(DeliveryRecord.order_id == order_id))
            row = result.scalar_one_or_none()
            return DeliveryProjection(**_load(row.payload)) if row else None
