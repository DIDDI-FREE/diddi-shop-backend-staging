from fastapi import APIRouter, Request

router = APIRouter(prefix="/internal/v1/support", tags=["support"])


@router.get("/orders/{order_id}/context")
async def order_context(order_id: str):
    return {"order_id": order_id, "owner": "diddishop", "status": "projection_not_configured"}


@router.get("/orders/{order_id}/context/live")
async def live_order_context(order_id: str, request: Request):
    return await request.app.state.support_context_service.build_order_context(order_id)
