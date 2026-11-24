from contextlib import asynccontextmanager

from fastapi import FastAPI

from app_base.core.outbox import OutboxMessage
from app_base.core.integration_registry import build_integrations
from app_base.core.settings import get_settings
from app_base.modules.orders.infra.repositories import InMemoryOrderRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.integrations = build_integrations(app.state.settings)
    app.state.order_repository = InMemoryOrderRepository()
    app.state.outbox: list[OutboxMessage] = []
    app.state.db_session_factory = lambda: None
    yield
    app.state.outbox.clear()
