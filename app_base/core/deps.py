from collections.abc import AsyncIterator

from fastapi import Request

from app_base.core.settings import Settings, get_settings
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.interfaces import OrderRepository


async def session_dep(request: Request) -> AsyncIterator[object]:
    """Central session seam; handlers never construct a DB session themselves."""
    factory = getattr(request.app.state, "db_session_factory", None)
    if factory is None:
        yield None
        return
    async with factory() as session:
        yield session


def get_app_settings() -> Settings:
    return get_settings()


def get_order_service(request: Request) -> OrderService:
    repository: OrderRepository = request.app.state.order_repository
    return OrderService(repository=repository, outbox=request.app.state.outbox)


def get_integrations(request: Request):
    return request.app.state.integrations
