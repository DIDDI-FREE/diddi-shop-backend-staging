"""Stable HTTP representations consumed by the web and mobile clients."""

from datetime import datetime
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
    title: str
    unit_price_minor: int = Field(ge=0)
    line_total_minor: int = Field(ge=0)


class CartShopSubtotalResponse(BaseModel):
    shop_id: str
    subtotal_minor: int = Field(ge=0)


class CartResponse(BaseModel):
    id: str
    customer_id: str
    currency: Literal["XOF"]
    lines: list[CartLineResponse]
    line_count: int = Field(ge=0)
    subtotal_minor: int = Field(ge=0)
    shop_subtotals: list[CartShopSubtotalResponse]


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
    items: list["OrderLineResponse"]
    subtotal_minor: int = Field(ge=0)
    delivery_fee_minor: int = Field(ge=0)
    discount_minor: int = Field(ge=0)
    created_at: str
    seller_confirmation_deadline: str | None
    recipient_name: str | None
    dropoff_address: str | None


class OrderLineResponse(BaseModel):
    product_id: str
    title: str
    unit_price_minor: int = Field(ge=0)
    quantity: int = Field(gt=0)
    line_total_minor: int = Field(ge=0)


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
    subtotal_minor: int = Field(ge=0)
    delivery_fee_minor: int = Field(ge=0)
    discount_minor: int = Field(ge=0)
    shop_breakdowns: list["CheckoutShopBreakdownResponse"]
    payment_attempt: int = Field(ge=1)
    created_at: str


class CheckoutShopBreakdownResponse(BaseModel):
    shop_id: str
    subtotal_minor: int = Field(ge=0)
    delivery_fee_minor: int = Field(ge=0)
    discount_minor: int = Field(ge=0)
    total_minor: int = Field(ge=0)


class CheckoutQuoteResponse(BaseModel):
    currency: Literal["XOF"]
    subtotal_minor: int = Field(ge=0)
    delivery_fee_minor: int = Field(ge=0)
    discount_minor: int = Field(ge=0)
    total_minor: int = Field(ge=0)
    shop_breakdowns: list[CheckoutShopBreakdownResponse]


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


class DeliveryResponse(BaseModel):
    id: str | None
    order_id: str
    status: Literal["not_requested", "requested", "assigned", "picked_up", "in_transit", "delivered", "failed", "returned"]
    proof_ref: str | None = None
    tracking: dict[str, Any] | None = None
    courier: dict[str, Any] | None = None
    dropoff_code: str | None = None
    position: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    service: str
    status: str


class ReadinessResponse(BaseModel):
    service: str
    status: Literal["ready", "not_ready"]
    dependencies: dict[str, Literal["ok", "error", "unknown"]]


class CampaignListResponse(BaseModel):
    items: list[dict[str, Any]]
    source: str
    mode: str


class AdminCapabilitiesResponse(BaseModel):
    service: str
    owner: str
    commands: list[str]
    note: str


class AdminOrderResponse(BaseModel):
    order: OrderResponse
    delivery_projection: DeliveryResponse | None


class SupportContextResponse(BaseModel):
    order: dict[str, Any]
    delivery: DeliveryResponse | None
    claim: "ClaimResponse | None"
    owner_service: str
    source_of_truth: dict[str, str]


class SupportCaseResponse(BaseModel):
    case: dict[str, Any]


class WebhookResponse(BaseModel):
    status: Literal["processed", "duplicate"]


class CommsHealthResponse(BaseModel):
    owner: str
    consumer: str


class RewardsHealthResponse(BaseModel):
    owner: str
    consumer: str
    mode: str


class ObservabilityHealthResponse(BaseModel):
    service: str
    status: str
    telemetry: dict[str, Any]


class ClaimResponse(BaseModel):
    id: str
    order_id: str
    customer_id: str
    reason: str
    opened_at: datetime
    status: Literal["open", "decided"]
    decision: Literal["buyer", "seller", "partial", "rejected"] | None = None
    amount_to_refund: int = Field(ge=0)
    decided_at: datetime | None = None


def claim_response(claim: Any) -> dict[str, Any]:
    return {
        "id": claim.id,
        "order_id": claim.order_id,
        "customer_id": claim.customer_id,
        "reason": claim.reason,
        "opened_at": claim.opened_at,
        "status": claim.status.value,
        "decision": claim.decision.value if claim.decision else None,
        "amount_to_refund": claim.amount_to_refund,
        "decided_at": claim.decided_at,
    }


def delivery_response(delivery: Any | None, order_id: str) -> dict[str, Any]:
    if delivery is None:
        return {"id": None, "order_id": order_id, "status": "not_requested"}
    return {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "status": delivery.status.value,
        "proof_ref": delivery.proof_ref,
        "tracking": delivery.tracking,
        "courier": delivery.courier,
        "dropoff_code": delivery.dropoff_code,
        "position": delivery.position,
    }


def admin_order_response(order: Any, delivery: Any | None) -> dict[str, Any]:
    return {"order": order_response(order), "delivery_projection": delivery_response(delivery, order.id) if delivery else None}


def support_context_response(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "order": order_response(context["order"]),
        "delivery": delivery_response(context["delivery"], context["order"].id) if context.get("delivery") else None,
        "claim": claim_response(context["claim"]) if context.get("claim") else None,
        "owner_service": context["owner_service"],
        "source_of_truth": context["source_of_truth"],
    }


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


def cart_response(
    cart: Cart,
    line_details: list[dict[str, Any]] | None = None,
    shop_subtotals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lines = line_details or [
        {
            "product_id": line.product_id,
            "shop_id": line.shop_id,
            "quantity": line.quantity,
            "title": "",
            "unit_price_minor": 0,
            "line_total_minor": 0,
        }
        for line in cart.lines
    ]
    return {
        "id": cart.id,
        "customer_id": cart.customer_id,
        "currency": "XOF",
        "lines": lines,
        "line_count": len(cart.lines),
        "subtotal_minor": sum(line.get("line_total_minor", 0) for line in lines),
        "shop_subtotals": shop_subtotals or [],
    }


def order_response(order: Order) -> dict[str, Any]:
    raw_lines = order.metadata.get("lines", [])
    lines = [
        {
            **line,
            "line_total_minor": line.get("line_total_minor", line.get("unit_price_minor", 0) * line.get("quantity", 0)),
        }
        for line in raw_lines
    ]
    delivery_request = order.metadata.get("delivery_request", {})
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
        "items": lines,
        "subtotal_minor": order.metadata.get("items_total", sum(line["line_total_minor"] for line in lines)),
        "delivery_fee_minor": order.metadata.get("delivery_fee", 0),
        "discount_minor": order.metadata.get("rewards_discount_minor", 0),
        "created_at": order.created_at,
        "seller_confirmation_deadline": order.seller_confirmation_deadline,
        "recipient_name": delivery_request.get("recipient_name"),
        "dropoff_address": delivery_request.get("dropoff_address"),
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
        "subtotal_minor": checkout.subtotal_minor,
        "delivery_fee_minor": checkout.delivery_fee_minor,
        "discount_minor": checkout.discount_minor,
        "shop_breakdowns": checkout.shop_breakdowns,
        "payment_attempt": checkout.payment_attempt,
        "created_at": checkout.created_at,
    }
