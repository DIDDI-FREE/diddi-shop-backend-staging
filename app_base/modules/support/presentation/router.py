from fastapi import APIRouter, Depends, Request

from app_base.core.api_contracts import (
    SupportCaseResponse,
    SupportContextResponse,
    support_context_response,
    support_context_stub_response,
)
from app_base.core.auth_deps import Actor, current_service_actor

router = APIRouter(prefix="/internal/v1/support", tags=["support"])


@router.get("/orders/{order_id}/context", response_model=SupportContextResponse)
@router.get("/order/{order_id}/context", response_model=SupportContextResponse, include_in_schema=False)
async def order_context(order_id: str, _actor: Actor = Depends(current_service_actor)):
    return support_context_stub_response(order_id)


@router.get("/orders/{order_id}/context/live", response_model=SupportContextResponse)
async def live_order_context(order_id: str, request: Request, _actor: Actor = Depends(current_service_actor)):
    return support_context_response(await request.app.state.support_context_service.build_order_context(order_id))


@router.post("/orders/{order_id}/cases", response_model=SupportCaseResponse)
async def open_case(order_id: str, request: Request, actor: Actor = Depends(current_service_actor)):
    context = await request.app.state.support_context_service.build_order_context(order_id)
    reason = "Order support request"
    claim = context.get("claim")
    if claim is not None:
        reason = claim.reason
    return {"case": await request.app.state.support_context_service.open_case(order_id, actor.subject, reason)}
