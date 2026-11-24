from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

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


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, body: CancelOrderRequest, service: FinanceService = Depends(finance_service)):
    return await service.cancel(order_id, body.reason)


@router.post("/orders/{order_id}")
async def open_claim(order_id: str, body: OpenClaimRequest, actor: Actor = Depends(current_actor), service: FinanceService = Depends(finance_service)):
    return await service.open_claim(order_id, actor.subject, body.reason)


@router.post("/{claim_id}/decision")
async def decide_claim(claim_id: str, body: DecideClaimRequest, service: FinanceService = Depends(finance_service)):
    return await service.decide(claim_id, body.decision, body.amount_to_refund)
