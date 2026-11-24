from fastapi import APIRouter, Depends, Request

from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.presentation import CreateProductRequest

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


def catalog_service(request: Request) -> CatalogService:
    return request.app.state.catalog_service


@router.post("/shops/{shop_id}/products")
async def create_product(shop_id: str, body: CreateProductRequest, actor: Actor = Depends(current_actor), service: CatalogService = Depends(catalog_service)):
    return await service.create(actor.subject, shop_id, **body.model_dump())


@router.post("/products/{product_id}/publish")
async def publish_product(product_id: str, actor: Actor = Depends(current_actor), service: CatalogService = Depends(catalog_service)):
    return await service.publish(actor.subject, product_id)


@router.get("/products/{product_id}")
async def get_product(product_id: str, service: CatalogService = Depends(catalog_service)):
    return await service.get(product_id)
