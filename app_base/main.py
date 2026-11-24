from fastapi import FastAPI

from app_base.core.lifespan import lifespan
from app_base.modules.admin.presentation.router import router as admin_router
from app_base.modules.campaigns.presentation.router import router as campaigns_router
from app_base.modules.comms.presentation.router import router as comms_router
from app_base.modules.observability.presentation.router import router as observability_router
from app_base.modules.orders.presentation.router import router as orders_router
from app_base.modules.rewards.presentation.router import router as rewards_router
from app_base.modules.support.presentation.router import router as support_router


app = FastAPI(title="DiddiShop", version="0.1.0", lifespan=lifespan)

app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(campaigns_router)
app.include_router(comms_router)
app.include_router(observability_router)
app.include_router(rewards_router)
app.include_router(support_router)


@app.get("/health", tags=["health"])
async def health():
    return {"service": "diddishop", "status": "ok"}


@app.get("/ready", tags=["health"])
async def ready():
    return {"service": "diddishop", "status": "ready", "dependencies": "skeleton"}
