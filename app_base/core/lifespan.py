from contextlib import asynccontextmanager

from fastapi import FastAPI

from app_base.core.outbox import OutboxMessage
from app_base.core.database import build_engine, build_session_factory
from app_base.core.integration_registry import build_integrations
from app_base.core.settings import get_settings
from redis.asyncio import Redis
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository
from app_base.modules.cart.application import CartService
from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.infra import InMemoryShopRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.integrations = build_integrations(app.state.settings)
    app.state.db_engine = build_engine(app.state.settings.database_url)
    app.state.db_session_factory = build_session_factory(app.state.db_engine)
    app.state.redis = Redis.from_url(app.state.settings.redis_url, decode_responses=False)
    app.state.order_repository = InMemoryOrderRepository()
    app.state.shop_repository = InMemoryShopRepository()
    app.state.product_repository = InMemoryProductRepository()
    app.state.cart_repository = InMemoryCartRepository()
    app.state.shop_service = ShopService(app.state.shop_repository)
    app.state.catalog_service = CatalogService(app.state.product_repository, app.state.shop_repository)
    app.state.cart_service = CartService(app.state.cart_repository, app.state.product_repository)
    app.state.outbox: list[OutboxMessage] = []
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.db_engine.dispose()
    app.state.outbox.clear()
