from contextlib import asynccontextmanager

from fastapi import FastAPI

from app_base.core.outbox import OutboxMessage
from app_base.core.database import build_engine, build_session_factory
from app_base.core.integration_registry import build_integrations
from app_base.core.settings import get_settings
from redis.asyncio import Redis
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository
from app_base.modules.orders.application.services import OrderService
from app_base.modules.cart.application import CartService
from app_base.modules.cart.infra import InMemoryCartRepository
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.infra import InMemoryProductRepository
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.infra import InMemoryShopRepository
from app_base.integrations.checkout_ports import DiddiPayPaymentIntentPort, DiddiSendDeliveryQuotePort
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.infra import InMemoryCheckoutRepository
from app_base.modules.delivery.application import DeliveryService
from app_base.modules.delivery.infra import InMemoryDeliveryRepository
from app_base.modules.webhooks import router as webhooks_router
from app_base.workers.in_memory_inbox import InMemoryProcessedEvents
from app_base.modules.claims.infra import InMemoryClaimRepository
from app_base.modules.finance import FinanceService
from app_base.modules.audit.application import AuditService
from app_base.modules.comms.application import CommunicationService
from app_base.modules.rewards.application import RewardsService
from app_base.modules.support.application import SupportContextService


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
    app.state.checkout_repository = InMemoryCheckoutRepository()
    app.state.checkout_service = CheckoutApplicationService(
        carts=app.state.cart_repository,
        products=app.state.product_repository,
        checkouts=app.state.checkout_repository,
        orders=app.state.order_repository,
        delivery_quotes=DiddiSendDeliveryQuotePort(app.state.integrations.diddisend),
        payments=DiddiPayPaymentIntentPort(app.state.integrations.diddipay),
        outbox=app.state.outbox,
    )
    app.state.processed_events = InMemoryProcessedEvents()
    app.state.delivery_repository = InMemoryDeliveryRepository()
    app.state.delivery_service = DeliveryService(
        app.state.delivery_repository,
        app.state.integrations.diddisend,
        OrderService(app.state.order_repository, app.state.outbox),
    )
    app.state.claim_repository = InMemoryClaimRepository()
    app.state.finance_service = FinanceService(
        OrderService(app.state.order_repository, app.state.outbox),
        app.state.claim_repository,
        app.state.integrations.diddipay,
        products=app.state.product_repository,
        delivery=app.state.integrations.diddisend,
    )
    app.state.rewards_service = RewardsService(app.state.integrations.diddirewards)
    app.state.communication_service = CommunicationService(app.state.integrations.diddicomms)
    app.state.audit_service = AuditService()
    app.state.support_context_service = SupportContextService(
        OrderService(app.state.order_repository, app.state.outbox),
        app.state.delivery_repository,
        app.state.claim_repository,
    )
    app.state.outbox: list[OutboxMessage] = []
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.db_engine.dispose()
    app.state.outbox.clear()
