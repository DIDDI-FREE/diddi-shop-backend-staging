from fastapi import APIRouter, Depends, Request

from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.presentation import CreateCheckoutRequest

router = APIRouter(prefix="/v1/checkouts", tags=["checkout"])


def checkout_service(request: Request) -> CheckoutApplicationService:
    return request.app.state.checkout_service


@router.post("")
async def create_checkout(body: CreateCheckoutRequest, actor: Actor = Depends(current_actor), service: CheckoutApplicationService = Depends(checkout_service)):
    context = body.model_dump(exclude={"idempotency_key"}, exclude_none=True)
    if {"dropoff_address", "dropoff_latitude", "dropoff_longitude"} <= context.keys():
        context["dropoff_location"] = {
            "lat": context.pop("dropoff_latitude"),
            "lng": context.pop("dropoff_longitude"),
            "address": context["dropoff_address"],
        }
    return await service.create(actor.subject, body.idempotency_key, context or None)
