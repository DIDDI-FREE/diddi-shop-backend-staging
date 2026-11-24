from fastapi import APIRouter

router = APIRouter(prefix="/internal/v1/observability", tags=["observability"])


@router.get("/health")
async def health():
    return {"service": "diddishop", "status": "ok"}
