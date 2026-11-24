from fastapi import APIRouter

router = APIRouter(prefix="/internal/v1/rewards", tags=["rewards"])


@router.get("/health")
async def health():
    return {"owner": "diddirewards", "consumer": "diddishop", "mode": "adapter_boundary"}
