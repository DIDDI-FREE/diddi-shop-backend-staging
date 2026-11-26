from fastapi import APIRouter, Depends

from app_base.core.api_contracts import CommsHealthResponse
from app_base.core.auth_deps import Actor, current_service_actor

router = APIRouter(prefix="/internal/v1/comms", tags=["comms"])


@router.get("/health", response_model=CommsHealthResponse)
async def health(_actor: Actor = Depends(current_service_actor)):
    return {"owner": "diddicomms", "consumer": "diddishop"}
