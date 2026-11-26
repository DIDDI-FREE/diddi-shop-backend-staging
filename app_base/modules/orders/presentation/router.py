from fastapi import APIRouter, Depends, HTTPException, Request

from app_base.core.api_contracts import OrderListResponse, OrderResponse, order_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.core.deps import get_order_service
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus

router = APIRouter(prefix="/v1/orders", tags=["orders"])


async def _authorize_order(request: Request, order_id: str, actor: Actor, *, seller_only: bool = False) -> None:
    if actor.actor_type in {"admin", "support", "service"}:
        return
    order = await request.app.state.order_service.get(order_id)
    shop = await request.app.state.shop_service.get(order.shop_id)
    buyer_id = order.metadata.get("delivery_request", {}).get("customer_user_id")
    if seller_only:
        if actor.subject != shop.owner_id:
            raise HTTPException(status_code=403, detail="seller access required")
        return
    if actor.subject not in {buyer_id, shop.owner_id}:
        raise HTTPException(status_code=403, detail="order access denied")


@router.get("", response_model=OrderListResponse)
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


@router.get("/seller/to-confirm", response_model=OrderListResponse)
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


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    try:
        await _authorize_order(request, order_id, actor)
        return order_response(await service.get(order_id))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{order_id}/transitions", response_model=OrderResponse)
async def transition_order(
    order_id: str,
    target: FulfillmentStatus,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    try:
        await _authorize_order(request, order_id, actor, seller_only=True)
        return order_response(await service.transition(order_id, target, reason="api_command", actor="api"))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: str,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    await _authorize_order(request, order_id, actor, seller_only=True)
    return order_response(await service.transition(order_id, FulfillmentStatus.TO_PREPARE, reason="seller_confirmed", actor="seller"))


@router.post("/{order_id}/ready", response_model=OrderResponse)
async def mark_order_ready(
    order_id: str,
    request: Request,
    actor: Actor = Depends(current_actor),
    service: OrderService = Depends(get_order_service),
):
    await _authorize_order(request, order_id, actor, seller_only=True)
    await request.app.state.delivery_service.mark_ready_and_request(order_id)
    return order_response(await service.get(order_id))
