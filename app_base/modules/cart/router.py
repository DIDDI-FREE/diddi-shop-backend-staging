from fastapi import APIRouter, Depends, Request

from app_base.core.api_contracts import cart_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.cart.application import CartService
from app_base.modules.cart.presentation import AddCartLineRequest

router = APIRouter(prefix="/v1/cart", tags=["cart"])


def cart_service(request: Request) -> CartService:
    return request.app.state.cart_service


@router.get("")
async def get_cart(actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    return cart_response(await service.get(actor.subject))


@router.post("/lines")
async def add_line(body: AddCartLineRequest, actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    return cart_response(await service.add(actor.subject, body.product_id, body.quantity))


@router.delete("/lines/{product_id}")
async def remove_line(product_id: str, actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    return cart_response(await service.remove(actor.subject, product_id))
