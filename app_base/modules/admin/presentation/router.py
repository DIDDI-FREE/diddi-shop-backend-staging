from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.claims.domain import ClaimDecision

router = APIRouter(prefix="/v1/admin/shop", tags=["admin-shop"])


@router.get("/capabilities")
async def capabilities():
    return {
        "service": "diddishop",
        "owner": "diddi-shop",
        "commands": ["read_order", "read_claim", "decide_claim", "retry_external_operation"],
        "note": "Backoffice calls these routes through a scoped adapter and records its own operator audit.",
    }


class AdminDecisionRequest(BaseModel):
    decision: ClaimDecision
    amount_to_refund: int = Field(default=0, ge=0)
    reason: str = Field(min_length=1, max_length=1000)


@router.get("/orders/{order_id}")
async def read_order(order_id: str, request: Request, actor: Actor = Depends(current_actor)):
    return await request.app.state.admin_service.read_order(order_id, actor.subject)


@router.post("/claims/{claim_id}/decision")
async def decide_claim(claim_id: str, body: AdminDecisionRequest, request: Request, actor: Actor = Depends(current_actor)):
    return await request.app.state.admin_service.decide_claim(
        claim_id, body.decision, body.amount_to_refund, actor.subject, body.reason
    )
