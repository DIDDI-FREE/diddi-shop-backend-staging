from fastapi import APIRouter, Depends, Request

from app_base.core.api_contracts import ShopListResponse, ShopResponse, shop_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.presentation import CreateShopRequest

router = APIRouter(prefix="/v1/shops", tags=["shops"])


def shop_service(request: Request) -> ShopService:
    return request.app.state.shop_service


@router.post("", response_model=ShopResponse)
async def create_shop(body: CreateShopRequest, actor: Actor = Depends(current_actor), service: ShopService = Depends(shop_service)):
    return shop_response(await service.create(actor.subject, body.name, body.pickup_address, body.pickup_latitude, body.pickup_longitude))


@router.get("/mine", response_model=ShopListResponse)
async def list_my_shops(actor: Actor = Depends(current_actor), service: ShopService = Depends(shop_service)):
    return {"items": [shop_response(shop) for shop in await service.list_for_owner(actor.subject)]}


@router.get("/{shop_id}", response_model=ShopResponse)
async def get_shop(shop_id: str, service: ShopService = Depends(shop_service)):
    return shop_response(await service.get_public(shop_id))
