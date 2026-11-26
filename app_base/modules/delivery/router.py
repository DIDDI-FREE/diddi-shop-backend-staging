from fastapi import APIRouter, Depends, HTTPException, Request

from app_base.core.api_contracts import DeliveryResponse, delivery_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.delivery.application import DeliveryService

router = APIRouter(prefix="/v1/deliveries", tags=["delivery"])


def delivery_service(request: Request) -> DeliveryService:
    return request.app.state.delivery_service


@router.post("/orders/{order_id}", response_model=DeliveryResponse)
async def request_delivery(
    order_id: str,
    actor: Actor = Depends(current_actor),
    service: DeliveryService = Depends(delivery_service),
):
    if actor.actor_type not in {"admin", "support", "service"}:
        raise HTTPException(status_code=403, detail="delivery retry requires an operator")
    return delivery_response(await service.request_for_order(order_id), order_id)


@router.get("/orders/{order_id}", response_model=DeliveryResponse)
async def get_delivery(order_id: str, request: Request, actor: Actor = Depends(current_actor)):
    delivery = await request.app.state.delivery_repository.get_by_order(order_id)
    if actor.actor_type not in {"admin", "support", "service"}:
        order = await request.app.state.order_service.get(order_id)
        shop = await request.app.state.shop_service.get(order.shop_id)
        buyer_id = order.metadata.get("delivery_request", {}).get("customer_user_id")
        if actor.subject not in {shop.owner_id, buyer_id}:
            raise HTTPException(status_code=403, detail="delivery access denied")
    return delivery_response(delivery, order_id)
