"""Stable HTTP representations consumed by the web and mobile clients."""

from typing import Any

from app_base.modules.cart.domain import Cart
from app_base.modules.catalog.domain import Product
from app_base.modules.checkout.domain import Checkout
from app_base.modules.orders.domain.entities import Order
from app_base.modules.shops.domain import Shop


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
