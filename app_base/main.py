from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app_base.core.errors import DiddiShopError
from app_base.core.lifespan import lifespan
from app_base.core.middleware import CorrelationMiddleware
from app_base.modules.admin.presentation.router import router as admin_router
from app_base.modules.campaigns.presentation.router import router as campaigns_router
from app_base.modules.cart.router import router as cart_router
from app_base.modules.catalog.router import router as catalog_router
from app_base.modules.checkout.router import router as checkout_router
from app_base.modules.claims.router import router as claims_router
from app_base.modules.comms.presentation.router import router as comms_router
from app_base.modules.delivery.router import router as delivery_router
from app_base.modules.observability.presentation.router import router as observability_router
from app_base.modules.orders.presentation.router import router as orders_router
from app_base.modules.rewards.presentation.router import router as rewards_router
from app_base.modules.shops.router import router as shops_router
from app_base.modules.support.presentation.router import router as support_router
from app_base.modules.webhooks import router as webhooks_router

app = FastAPI(title="DiddiShop", version="0.1.0", lifespan=lifespan)
app.add_middleware(CorrelationMiddleware)


@app.exception_handler(DiddiShopError)
async def handle_domain_error(_request: Request, exc: DiddiShopError):
    return JSONResponse(status_code=409, content={"error": type(exc).__name__, "message": str(exc)})

app.include_router(orders_router)
app.include_router(shops_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(checkout_router)
app.include_router(delivery_router)
app.include_router(claims_router)
app.include_router(admin_router)
app.include_router(campaigns_router)
app.include_router(comms_router)
app.include_router(observability_router)
app.include_router(rewards_router)
app.include_router(support_router)
app.include_router(webhooks_router)


@app.get("/health", tags=["health"])
async def health():
    return {"service": "diddishop", "status": "ok"}


@app.get("/ready", tags=["health"])
async def ready(request: Request):
    dependencies = {"postgres": "unknown", "redis": "unknown"}
    try:
        async with request.app.state.db_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "error"
    try:
        await request.app.state.redis.ping()
        dependencies["redis"] = "ok"
    except Exception:
        dependencies["redis"] = "error"
    status = "ready" if all(value == "ok" for value in dependencies.values()) else "not_ready"
    return {"service": "diddishop", "status": status, "dependencies": dependencies}
