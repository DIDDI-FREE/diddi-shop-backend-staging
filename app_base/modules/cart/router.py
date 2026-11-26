from fastapi import APIRouter, Depends, Request

from app_base.core.api_contracts import CartResponse, cart_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.cart.application import CartService
from app_base.modules.cart.presentation import AddCartLineRequest

router = APIRouter(prefix="/v1/cart", tags=["cart"])


def cart_service(request: Request) -> CartService:
    return request.app.state.cart_service


@router.get("", response_model=CartResponse)
async def get_cart(actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    cart, details, shop_subtotals = await service.details(actor.subject)
    return cart_response(cart, details, shop_subtotals)


@router.post("/lines", response_model=CartResponse)
async def add_line(body: AddCartLineRequest, actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    await service.add(actor.subject, body.product_id, body.quantity)
    cart, details, shop_subtotals = await service.details(actor.subject)
    return cart_response(cart, details, shop_subtotals)


@router.delete("/lines/{product_id}", response_model=CartResponse)
async def remove_line(product_id: str, actor: Actor = Depends(current_actor), service: CartService = Depends(cart_service)):
    await service.remove(actor.subject, product_id)
    cart, details, shop_subtotals = await service.details(actor.subject)
    return cart_response(cart, details, shop_subtotals)
