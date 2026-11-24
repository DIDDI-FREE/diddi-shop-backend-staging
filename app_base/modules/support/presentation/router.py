from fastapi import APIRouter, Depends, Request

from app_base.core.auth_deps import Actor, current_actor

router = APIRouter(prefix="/internal/v1/support", tags=["support"])


@router.get("/orders/{order_id}/context")
async def order_context(order_id: str):
    return {"order_id": order_id, "owner": "diddishop", "status": "projection_not_configured"}


@router.get("/orders/{order_id}/context/live")
async def live_order_context(order_id: str, request: Request):
    return await request.app.state.support_context_service.build_order_context(order_id)


@router.post("/orders/{order_id}/cases")
async def open_case(order_id: str, request: Request, actor: Actor = Depends(current_actor)):
    context = await request.app.state.support_context_service.build_order_context(order_id)
    reason = "Order support request"
    claim = context.get("claim")
    if claim is not None:
        reason = claim.reason
    return await request.app.state.support_context_service.open_case(order_id, actor.subject, reason)
