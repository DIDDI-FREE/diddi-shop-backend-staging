from fastapi import APIRouter

from app_base.core.api_contracts import CampaignListResponse

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


@router.get("/active", response_model=CampaignListResponse)
async def active_campaigns():
    return {"items": [], "source": "diddirewards", "mode": "projection_not_configured"}
