from fastapi import APIRouter, Request

router = APIRouter(prefix="/internal/v1/observability", tags=["observability"])


@router.get("/health")
async def health(request: Request):
    runtime = getattr(request.app.state, "telemetry", None)
    return {
        "service": "diddishop",
        "status": "ok",
        "telemetry": runtime.stats.snapshot() if runtime is not None else {},
    }
