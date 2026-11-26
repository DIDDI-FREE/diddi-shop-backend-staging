from fastapi import APIRouter, Depends, HTTPException, Request

from app_base.core.api_contracts import order_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.core.deps import get_order_service
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus

router = APIRouter(prefix="/v1/orders", tags=["orders"])


@router.get("")
async def list_my_orders(
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    checkouts = await request.app.state.checkout_repository.list_for_customer(actor.subject)
    orders = []
    seen: set[str] = set()
    for checkout in checkouts:
        for order_id in checkout.order_ids:
            if order_id in seen:
                continue
            seen.add(order_id)
            orders.append(order_response(await service.get(order_id)))
    return {"items": orders}


@router.get("/seller/to-confirm")
async def list_orders_to_confirm(
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    shops = await request.app.state.shop_service.list_for_owner(actor.subject)
    orders = []
    for shop in shops:
        orders.extend(
            order_response(order)
            for order in await service.list_for_shop(shop.id, status=FulfillmentStatus.TO_CONFIRM)
        )
    return {"items": orders}


@router.get("/{order_id}")
async def get_order(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return order_response(await service.get(order_id))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{order_id}/transitions")
async def transition_order(order_id: str, target: FulfillmentStatus, service: OrderService = Depends(get_order_service)):
    try:
        return order_response(await service.transition(order_id, target, reason="api_command", actor="api"))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/confirm")
async def confirm_order(order_id: str, service: OrderService = Depends(get_order_service)):
    return order_response(await service.transition(order_id, FulfillmentStatus.TO_PREPARE, reason="seller_confirmed", actor="seller"))


@router.post("/{order_id}/ready")
async def mark_order_ready(order_id: str, service: OrderService = Depends(get_order_service)):
    order = await service.transition(order_id, FulfillmentStatus.READY_FOR_PICKUP, reason="seller_ready", actor="seller")
    return order_response(order)
