from fastapi import APIRouter, Depends, Request

from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.presentation import CreateCheckoutRequest

router = APIRouter(prefix="/v1/checkouts", tags=["checkout"])


def checkout_service(request: Request) -> CheckoutApplicationService:
    return request.app.state.checkout_service


@router.post("")
async def create_checkout(body: CreateCheckoutRequest, actor: Actor = Depends(current_actor), service: CheckoutApplicationService = Depends(checkout_service)):
    return await service.create(actor.subject, body.idempotency_key)
