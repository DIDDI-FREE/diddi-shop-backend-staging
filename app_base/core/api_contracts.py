"""Stable HTTP representations consumed by the web and mobile clients."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app_base.modules.cart.domain import Cart
from app_base.modules.catalog.domain import Product
from app_base.modules.checkout.domain import Checkout
from app_base.modules.orders.domain.entities import Order
from app_base.modules.shops.domain import Shop


class ProductResponse(BaseModel):
    id: str
    shop_id: str
    title: str
    description: str
    price_minor: int
    currency: Literal["XOF"]
    stock: int
    category: str
    status: Literal["draft", "published", "paused", "retired"]
    photo_file_ids: list[str]
    photo_urls: list[str]


class ProductListResponse(BaseModel):
    items: list[ProductResponse]


class ShopResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    status: Literal["active", "suspended"]


class ShopListResponse(BaseModel):
    items: list[ShopResponse]


class CategoryResponse(BaseModel):
    code: str
    name: str


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]


class CartLineResponse(BaseModel):
    product_id: str
    shop_id: str
    quantity: int = Field(ge=1)


class CartResponse(BaseModel):
    id: str
    customer_id: str
    currency: Literal["XOF"]
    lines: list[CartLineResponse]
    line_count: int = Field(ge=0)


class OrderResponse(BaseModel):
    id: str
    shop_id: str
    checkout_id: str
    total_minor: int
    currency: Literal["XOF"]
    fulfillment_status: Literal[
        "PAYMENT_PENDING",
        "TO_CONFIRM",
        "TO_PREPARE",
        "READY_FOR_PICKUP",
        "PICKED_UP",
        "IN_TRANSIT",
        "DELIVERED",
        "RETURNED",
        "CANCELLED",
        "FAILED",
        "DISPUTED",
        "CLOSED",
    ]
    payment_status: Literal[
        "PENDING",
        "HELD",
        "REFUND_PENDING",
        "REFUNDED",
        "RELEASE_BLOCKED",
        "RELEASE_PENDING",
        "RELEASED",
        "PARTIALLY_REFUNDED",
    ]
    delivery_id: str | None
    version: int = Field(ge=0)
    payment_intent_id: str | None
    items: list[dict[str, Any]]


class OrderListResponse(BaseModel):
    items: list[OrderResponse]


class CheckoutPaymentResponse(BaseModel):
    payment_intent_id: str | None
    amount_minor: int
    currency: Literal["XOF"]
    status: str
    payment_url: str | None = None
    checkout_url: str | None = None
    client_secret: str | None = None


class CheckoutResponse(BaseModel):
    id: str
    customer_id: str
    total_minor: int
    currency: Literal["XOF"]
    status: Literal["payment_pending", "payment_succeeded", "payment_failed"]
    order_ids: list[str]
    payment: CheckoutPaymentResponse


class ProductPhotoResponse(BaseModel):
    file_id: str
    url: str


class ProductPhotoListResponse(BaseModel):
    items: list[ProductPhotoResponse]


class UploadUrlResponse(BaseModel):
    method: Literal["PUT"] = "PUT"
    url: str
    expires_in_seconds: int
    headers: dict[str, str]


class UploadSessionResponse(BaseModel):
    file_id: str
    status: str
    upload: UploadUrlResponse


def product_response(product: Product, photo_urls: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": product.id,
        "shop_id": product.shop_id,
        "title": product.title,
        "description": product.description,
        "price_minor": product.price_minor,
        "currency": product.currency,
        "stock": product.stock,
        "category": product.category,
        "status": product.status.value,
        "photo_file_ids": list(product.photo_file_ids),
        "photo_urls": photo_urls or [],
    }


def shop_response(shop: Shop) -> dict[str, Any]:
    return {
        "id": shop.id,
        "owner_id": shop.owner_id,
        "name": shop.name,
        "pickup_address": shop.pickup_address,
        "pickup_latitude": shop.pickup_latitude,
        "pickup_longitude": shop.pickup_longitude,
        "status": shop.status.value,
    }


def cart_response(cart: Cart) -> dict[str, Any]:
    return {
        "id": cart.id,
        "customer_id": cart.customer_id,
        "currency": "XOF",
        "lines": [
            {
                "product_id": line.product_id,
                "shop_id": line.shop_id,
                "quantity": line.quantity,
            }
            for line in cart.lines
        ],
        "line_count": len(cart.lines),
    }


def order_response(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "shop_id": order.shop_id,
        "checkout_id": order.checkout_id,
        "total_minor": order.total_minor,
        "currency": order.currency,
        "fulfillment_status": order.fulfillment_status.value,
        "payment_status": order.payment_status.value,
        "delivery_id": order.delivery_id,
        "version": order.version,
        "payment_intent_id": order.metadata.get("payment_intent_id"),
        "items": order.metadata.get("lines", []),
    }


def checkout_response(checkout: Checkout, payment: dict[str, Any] | None = None) -> dict[str, Any]:
    source = payment or {}
    payment_response = {
        "payment_intent_id": checkout.payment_intent_id or source.get("payment_intent_id"),
        "amount_minor": source.get("amount_minor", checkout.total_minor),
        "currency": source.get("currency", checkout.currency),
        "status": source.get("status", "pending"),
    }
    for key in ("payment_url", "checkout_url", "client_secret"):
        if source.get(key) is not None:
            payment_response[key] = source[key]
    return {
        "id": checkout.id,
        "customer_id": checkout.customer_id,
        "total_minor": checkout.total_minor,
        "currency": checkout.currency,
        "status": checkout.status.value,
        "order_ids": list(checkout.order_ids),
        "payment": payment_response,
    }
