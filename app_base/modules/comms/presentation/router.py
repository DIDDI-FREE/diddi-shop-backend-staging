from fastapi import APIRouter

router = APIRouter(prefix="/internal/v1/comms", tags=["comms"])


@router.get("/health")
async def health():
    return {"owner": "diddicomms", "consumer": "diddishop"}
