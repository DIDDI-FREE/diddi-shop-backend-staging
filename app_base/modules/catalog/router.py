from fastapi import APIRouter, Depends, Query, Request

from app_base.core.api_contracts import (
    CategoryListResponse,
    ProductListResponse,
    ProductPhotoListResponse,
    ProductResponse,
    UploadSessionResponse,
    product_response,
)
from app_base.core.auth_deps import Actor, current_actor
from app_base.modules.catalog.application import CatalogService
from app_base.modules.catalog.domain import PRODUCT_CATEGORIES
from app_base.modules.catalog.presentation import (
    AttachProductPhotoRequest,
    CreatePhotoUploadSessionRequest,
    CreateProductRequest,
    UpdateProductRequest,
)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


def catalog_service(request: Request) -> CatalogService:
    return request.app.state.catalog_service


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories():
    return {"items": [{"code": code, "name": name} for code, name in PRODUCT_CATEGORIES]}


@router.post("/shops/{shop_id}/products", response_model=ProductResponse)
async def create_product(shop_id: str, body: CreateProductRequest, actor: Actor = Depends(current_actor), service: CatalogService = Depends(catalog_service)):
    return product_response(await service.create(actor.subject, shop_id, **body.model_dump()))


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    service: CatalogService = Depends(catalog_service),
):
    products = await service.list_published(category=category, search=search)
    return {"items": [product_response(product, await service.photo_urls(product)) for product in products]}


@router.get("/shops/{shop_id}/products", response_model=ProductListResponse)
async def list_shop_products(
    shop_id: str,
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    service: CatalogService = Depends(catalog_service),
):
    products = await service.list_published(shop_id=shop_id, category=category, search=search)
    return {"items": [product_response(product, await service.photo_urls(product)) for product in products]}


@router.get("/my-products", response_model=ProductListResponse)
async def list_my_products(
    shop_id: str | None = Query(default=None),
    actor: Actor = Depends(current_actor),
    service: CatalogService = Depends(catalog_service),
):
    products = await service.list_for_owner(actor.subject, shop_id)
    return {"items": [product_response(product, await service.photo_urls(product)) for product in products]}


@router.post("/products/{product_id}/publish", response_model=ProductResponse)
async def publish_product(product_id: str, actor: Actor = Depends(current_actor), service: CatalogService = Depends(catalog_service)):
    return product_response(await service.publish(actor.subject, product_id))


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    body: UpdateProductRequest,
    actor: Actor = Depends(current_actor),
    service: CatalogService = Depends(catalog_service),
):
    return product_response(await service.update(actor.subject, product_id, **body.model_dump(exclude_unset=True)))


@router.post("/products/{product_id}/photos/upload-session", response_model=UploadSessionResponse)
async def create_photo_upload_session(
    product_id: str,
    body: CreatePhotoUploadSessionRequest,
    actor: Actor = Depends(current_actor),
    service: CatalogService = Depends(catalog_service),
):
    return await service.create_photo_upload_session(actor.subject, product_id, **body.model_dump())


@router.post("/products/{product_id}/photos", response_model=ProductResponse)
async def attach_product_photo(
    product_id: str,
    body: AttachProductPhotoRequest,
    actor: Actor = Depends(current_actor),
    service: CatalogService = Depends(catalog_service),
):
    return product_response(await service.add_photo(actor.subject, product_id, body.file_id))


@router.get("/products/{product_id}/photos", response_model=ProductPhotoListResponse)
async def get_product_photos(product_id: str, service: CatalogService = Depends(catalog_service)):
    product = await service.get(product_id)
    urls = await service.photo_urls(product)
    return {
        "items": [
            {"file_id": file_id, "url": url}
            for file_id, url in zip(product.photo_file_ids, urls, strict=True)
        ]
    }


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, service: CatalogService = Depends(catalog_service)):
    product = await service.get(product_id)
    return product_response(product, await service.photo_urls(product))
