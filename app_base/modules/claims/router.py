from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app_base.core.api_contracts import (
    ClaimResponse,
    OrderResponse,
    UploadSessionResponse,
    claim_response,
    order_response,
)
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.claims.domain import ClaimDecision
from app_base.modules.finance import FinanceService
from app_base.shared_kernel.money import XofAmount

router = APIRouter(prefix="/v1/claims", tags=["claims"])


def finance_service(request: Request) -> FinanceService:
    return request.app.state.finance_service


class OpenClaimRequest(BaseModel):
    reason_code: Literal["not_as_described", "damaged", "incomplete", "missing_item", "other"] = "other"
    reason: str | None = Field(default=None, max_length=2000)
    evidence_file_ids: list[str] = Field(default_factory=list, max_length=3)


class DecideClaimRequest(BaseModel):
    decision: ClaimDecision
    amount_to_refund: XofAmount = Field(default=0, ge=0)


class CancelOrderRequest(BaseModel):
    reason: str = Field(default="buyer_requested", min_length=1, max_length=500)


class ClaimEvidenceUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)


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


async def _validate_evidence(request: Request, file_ids: list[str]) -> None:
    if len(file_ids) > 3:
        raise HTTPException(status_code=422, detail="at most 3 evidence photos are allowed")
    files = request.app.state.integrations.diddifiles
    for file_id in file_ids:
        await files.confirm_upload(file_id)
        metadata = await files.metadata(file_id)
        if metadata.get("purpose") != "diddishop_claim_evidence":
            raise HTTPException(status_code=409, detail="file purpose is not claim evidence")
        if metadata.get("mime_type") and metadata["mime_type"] not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=422, detail="unsupported evidence image format")


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
    await _validate_evidence(request, body.evidence_file_ids)
    reason = body.reason or body.reason_code
    return claim_response(await service.open_claim(
        order_id,
        actor.subject,
        reason,
        reason_code=body.reason_code,
        evidence_file_ids=body.evidence_file_ids,
    ))


@router.get("/orders/{order_id}", response_model=ClaimResponse)
async def get_claim(
    order_id: str,
    request: Request,
    actor: Actor = Depends(current_actor),
):
    await _authorize_order(request, order_id, actor)
    claim = await request.app.state.claim_repository.get_for_order(order_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return claim_response(claim)


@router.post("/orders/{order_id}/evidence/upload-session", response_model=UploadSessionResponse)
async def create_claim_evidence_upload_session(
    order_id: str,
    body: ClaimEvidenceUploadRequest,
    request: Request,
    actor: Actor = Depends(current_actor),
):
    await _authorize_order(request, order_id, actor)
    return await request.app.state.integrations.diddifiles.create_upload_session({
        "filename": body.filename,
        "mime_type": body.content_type,
        "size_bytes": body.size_bytes,
        "module_owner": "diddishop",
        "purpose": "diddishop_claim_evidence",
        "metadata": {"order_id": order_id},
    })


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
