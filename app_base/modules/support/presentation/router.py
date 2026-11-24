from fastapi import APIRouter

router = APIRouter(prefix="/internal/v1/support", tags=["support"])


@router.get("/orders/{order_id}/context")
async def order_context(order_id: str):
    return {"order_id": order_id, "owner": "diddishop", "status": "projection_not_configured"}
