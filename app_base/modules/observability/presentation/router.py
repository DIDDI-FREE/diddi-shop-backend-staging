from fastapi import APIRouter, Depends, Request

from app_base.core.api_contracts import ObservabilityHealthResponse
from app_base.core.auth_deps import Actor, current_service_actor

router = APIRouter(prefix="/internal/v1/observability", tags=["observability"])


@router.get("/health", response_model=ObservabilityHealthResponse)
async def health(request: Request, _actor: Actor = Depends(current_service_actor)):
    runtime = getattr(request.app.state, "telemetry", None)
    return {
        "service": "diddishop",
        "status": "ok",
        "telemetry": runtime.stats.snapshot() if runtime is not None else {},
    }
