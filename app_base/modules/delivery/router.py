from fastapi import APIRouter, Depends, Request

from app_base.modules.delivery.application import DeliveryService

router = APIRouter(prefix="/v1/deliveries", tags=["delivery"])


def delivery_service(request: Request) -> DeliveryService:
    return request.app.state.delivery_service


@router.post("/orders/{order_id}")
async def request_delivery(order_id: str, service: DeliveryService = Depends(delivery_service)):
    return await service.request_for_order(order_id)


@router.get("/orders/{order_id}")
async def get_delivery(order_id: str, request: Request):
    delivery = await request.app.state.delivery_repository.get_by_order(order_id)
    return delivery or {"order_id": order_id, "status": "not_requested"}
