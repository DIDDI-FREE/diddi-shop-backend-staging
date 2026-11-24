from fastapi import APIRouter, Depends, HTTPException

from app_base.core.deps import get_order_service
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus

router = APIRouter(prefix="/v1/orders", tags=["orders"])


@router.get("/{order_id}")
async def get_order(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return await service.get(order_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{order_id}/transitions")
async def transition_order(order_id: str, target: FulfillmentStatus, service: OrderService = Depends(get_order_service)):
    try:
        return await service.transition(order_id, target, reason="api_command", actor="api")
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
