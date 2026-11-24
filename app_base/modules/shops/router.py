from fastapi import APIRouter, Depends, Request

from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.presentation import CreateShopRequest

router = APIRouter(prefix="/v1/shops", tags=["shops"])


def shop_service(request: Request) -> ShopService:
    return request.app.state.shop_service


@router.post("")
async def create_shop(body: CreateShopRequest, actor: Actor = Depends(current_actor), service: ShopService = Depends(shop_service)):
    return await service.create(actor.subject, body.name, body.pickup_address, body.pickup_latitude, body.pickup_longitude)


@router.get("/{shop_id}")
async def get_shop(shop_id: str, actor: Actor = Depends(current_actor), service: ShopService = Depends(shop_service)):
    return await service.get_owned(shop_id, actor.subject)
