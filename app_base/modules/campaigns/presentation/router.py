from fastapi import APIRouter

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


@router.get("/active")
async def active_campaigns():
    return {"items": [], "source": "diddirewards", "mode": "projection_not_configured"}
