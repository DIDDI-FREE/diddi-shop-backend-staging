from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app_base.core.api_contracts import ClaimResponse, OrderResponse, claim_response, order_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.claims.domain import ClaimDecision
from app_base.modules.finance import FinanceService

router = APIRouter(prefix="/v1/claims", tags=["claims"])


def finance_service(request: Request) -> FinanceService:
    return request.app.state.finance_service


class OpenClaimRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class DecideClaimRequest(BaseModel):
    decision: ClaimDecision
    amount_to_refund: int = Field(default=0, ge=0)


class CancelOrderRequest(BaseModel):
    reason: str = Field(default="buyer_requested", min_length=1, max_length=500)


async def _authorize_order(request: Request, order_id: str, actor: Actor, *, operator_only: bool = False) -> None:
    if actor.actor_type in {"admin", "support", "service"}:
        return
    if operator_only:
        raise HTTPException(status_code=403, detail="operator access required")
    order = await request.app.state.order_service.get(order_id)
    shop = await request.app.state.shop_service.get(order.shop_id)
    buyer_id = order.metadata.get("delivery_request", {}).get("customer_user_id")
    if actor.subject not in {buyer_id, shop.owner_id}:
        raise HTTPException(status_code=403, detail="order access denied")


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    body: CancelOrderRequest,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: FinanceService = Depends(finance_service),
):
    await _authorize_order(request, order_id, actor)
    return order_response(await service.cancel(order_id, body.reason))


@router.post("/orders/{order_id}", response_model=ClaimResponse)
async def open_claim(
    order_id: str,
    body: OpenClaimRequest,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: FinanceService = Depends(finance_service),
):
    await _authorize_order(request, order_id, actor)
    return claim_response(await service.open_claim(order_id, actor.subject, body.reason))


@router.post("/{claim_id}/decision", response_model=ClaimResponse)
async def decide_claim(
    claim_id: str,
    body: DecideClaimRequest,
    actor: Actor = Depends(current_actor),
    service: FinanceService = Depends(finance_service),
):
    if actor.actor_type not in {"admin", "support", "service"}:
        raise HTTPException(status_code=403, detail="operator access required")
    return claim_response(await service.decide(claim_id, body.decision, body.amount_to_refund))
