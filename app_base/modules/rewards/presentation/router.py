from fastapi import APIRouter, Depends

from app_base.core.api_contracts import RewardsHealthResponse
from app_base.core.auth_deps import Actor, current_service_actor

router = APIRouter(prefix="/internal/v1/rewards", tags=["rewards"])


@router.get("/health", response_model=RewardsHealthResponse)
async def health(_actor: Actor = Depends(current_service_actor)):
    return {"owner": "diddirewards", "consumer": "diddishop", "mode": "adapter_boundary"}
