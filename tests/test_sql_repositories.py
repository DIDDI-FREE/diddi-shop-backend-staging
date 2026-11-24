import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app_base.core.business_repositories import SqlCartRepository, SqlProductRepository
from app_base.core.platform_models import Base
from app_base.modules.cart.domain import CartLine
from app_base.modules.catalog.domain import Product, ProductStatus


@pytest.mark.asyncio
async def test_sql_product_stock_operation_is_idempotent_and_persists():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    products = SqlProductRepository(factory)
    product = Product("product-1", "shop-1", "Item", "Description", 1000, "XOF", 2, "cat", [], ProductStatus.PUBLISHED)
    await products.save(product)
    await products.apply_stock(product.id, -1, "checkout-1")
    await products.apply_stock(product.id, -1, "checkout-1")
    assert (await products.get(product.id)).stock == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_cart_round_trip_rehydrates_cart_lines():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    carts = SqlCartRepository(factory)
    cart = await carts.get_or_create("customer-1")
    cart.lines.append(CartLine("product-1", "shop-1", 2))
    await carts.save(cart)
    loaded = await carts.get_or_create("customer-1")
    assert loaded.lines[0].product_id == "product-1"
    assert loaded.lines[0].quantity == 2
    await engine.dispose()
