from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app_base.core.api_contracts import (
    AdminCapabilitiesResponse,
    AdminOrderResponse,
    ClaimResponse,
    admin_order_response,
    claim_response,
)
from app_base.core.auth_deps import Actor, current_actor
from app_base.core.idempotency import IdempotencyRecord, replay_or_none, request_hash
from app_base.modules.claims.domain import ClaimDecision

router = APIRouter(prefix="/v1/admin/shop", tags=["admin-shop"])


async def admin_actor(request: Request, actor: Actor = Depends(current_actor)) -> Actor:
    if request.app.state.settings.environment == "development":
        return actor
    if actor.actor_type not in {"admin", "support", "service"}:
        raise HTTPException(status_code=403, detail="admin actor required")
    return actor


@router.get("/capabilities", response_model=AdminCapabilitiesResponse)
async def capabilities(_actor: Actor = Depends(admin_actor)):
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


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
async def read_order(order_id: str, request: Request, actor: Actor = Depends(admin_actor)):
    result = await request.app.state.admin_service.read_order(order_id, actor.subject)
    return admin_order_response(result["order"], result["delivery_projection"])


@router.post("/claims/{claim_id}/decision", response_model=ClaimResponse)
async def decide_claim(
    claim_id: str,
    body: AdminDecisionRequest,
    request: Request,
    actor: Actor = Depends(admin_actor),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    store = request.app.state.idempotency_store_factory(f"admin:claim:{claim_id}")
    body_data = body.model_dump(mode="json")
    replay = await replay_or_none(store, idempotency_key, body_data)
    if replay is not None:
        return replay.response_body
    result = await request.app.state.admin_service.decide_claim(
        claim_id, body.decision, body.amount_to_refund, actor.subject, body.reason
    )
    response_body = claim_response(result)
    await store.save(IdempotencyRecord(idempotency_key, request_hash(body_data), 200, response_body))
    return response_body
