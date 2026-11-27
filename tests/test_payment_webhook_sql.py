"""Signed callbacks and seller flow through real SQL repositories, no external calls."""

import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app_base.core.auth_deps import Actor, current_actor
from app_base.core.business_repositories import (
    SqlCartRepository,
    SqlCheckoutRepository,
    SqlDeliveryRepository,
    SqlOrderRepository,
    SqlProductRepository,
    SqlShopRepository,
)
from app_base.core.durable_stores import SqlInboxStore, SqlOutboxStore
from app_base.core.errors import DiddiShopError
from app_base.core.platform_models import Base
from app_base.main import handle_domain_error, handle_http_error
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.domain import Checkout, CheckoutStatus
from app_base.modules.checkout.router import router as checkout_router
from app_base.modules.delivery.application import DeliveryService
from app_base.modules.delivery.domain import DeliveryProjection, DeliveryStatus
from app_base.modules.delivery.router import router as delivery_router
from app_base.modules.orders.application.services import OrderService
from app_base.modules.orders.domain.entities import FulfillmentStatus, Order, PaymentStatus
from app_base.modules.orders.presentation.router import router as order_router
from app_base.modules.rewards.application import RewardsService
from app_base.modules.shops.application import ShopService
from app_base.modules.shops.domain import Shop, ShopStatus
from app_base.modules.shops.router import router as shop_router
from app_base.modules.webhooks import router as webhook_router
from app_base.shared_kernel.contracts.rewards import CampaignSnapshot, RewardReservation

SECRET = "synthetic-local-webhook-secret"
# Optional PostgreSQL check is restricted to the disposable Docker test database.
POSTGRES_TEST_URL = "postgresql+asyncpg://shop_test:shop_test@diddishop-webhook-test-db:5432/diddishop_test"


@asynccontextmanager
async def webhook_api():
    database_url = os.getenv("DIDDI_SHOP_TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    assert database_url in {"sqlite+aiosqlite:///:memory:", POSTGRES_TEST_URL}
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    shops = SqlShopRepository(factory)
    orders = SqlOrderRepository(factory)
    checkouts = SqlCheckoutRepository(factory)
    deliveries = SqlDeliveryRepository(factory)
    inbox = SqlInboxStore(factory)
    outbox = SqlOutboxStore(factory)
    order_service = OrderService(orders, outbox)

    class NoPayments:
        async def create_with_options(self, *args, **kwargs):
            raise AssertionError("A webhook must never start another payment")

    class Sender:
        def __init__(self):
            self.calls = []

        async def create_delivery(self, command, payload):
            self.calls.append((command, payload))
            return {"delivery": {"id": "delivery-test", "status": "created"}}

    sender = Sender()
    checkout_service = CheckoutApplicationService(
        SqlCartRepository(factory), SqlProductRepository(factory), checkouts,
        orders, None, NoPayments(), outbox,
    )
    app = FastAPI()
    for router in (webhook_router, checkout_router, order_router, shop_router, delivery_router):
        app.include_router(router)
    app.add_exception_handler(DiddiShopError, handle_domain_error)
    app.add_exception_handler(HTTPException, handle_http_error)
    app.state.settings = SimpleNamespace(
        environment="staging", diddipay_webhook_secret=SECRET, diddisend_webhook_secret=SECRET,
    )
    app.state.processed_events = inbox
    app.state.outbox = outbox
    app.state.shop_service = ShopService(shops)
    app.state.order_service = order_service
    app.state.order_repository = orders
    app.state.checkout_service = checkout_service
    app.state.checkout_repository = checkouts
    app.state.delivery_service = DeliveryService(deliveries, sender, order_service)
    app.state.delivery_repository = deliveries
    actor = SimpleNamespace(value=Actor("buyer", "user"))
    app.dependency_overrides[current_actor] = lambda: actor.value
    await shops.save(Shop("shop", "seller", "Test shop", "Pickup", 5.3, -4.0))
    await orders.create(Order(
        "order", "shop", "checkout", 5640,
        metadata={"delivery_request": {"customer_user_id": "buyer", "recipient_name": "Test"}},
    ))
    await checkouts.save(Checkout(
        "checkout", "buyer", 5640, "XOF", ["order"], "intent-test",
        payment={"status": "requires_action", "provider_status": "page_created"},
    ))
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app, raise_app_exceptions=False), base_url="https://shop.test",
        ) as client:
            yield SimpleNamespace(
                client=client, app=app, actor=actor, orders=orders, shops=shops,
                checkouts=checkouts, deliveries=deliveries, inbox=inbox, outbox=outbox, sender=sender,
            )
    finally:
        await engine.dispose()


def payment_event(event_id="payment-event"):
    return {
        "id": event_id, "type": "payment.succeeded", "occurred_at": "2026-11-27T12:00:00Z",
        "data": {"payment_intent_id": "intent-test", "business_reference": "diddishop:checkout:checkout",
                 "amount": 5640, "currency": "XOF"},
    }


async def signed_post(client, provider, event, secret=SECRET):
    body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    header = "X-DiddiPay-Signature" if provider == "diddipay" else "X-DiddiSend-Signature"
    return await client.post(
        f"/internal/v1/webhooks/{provider}", content=body,
        headers={"Content-Type": "application/json", header: signature},
    )


@pytest.mark.asyncio
async def test_signed_success_sql_readback_seller_and_delivery_lifecycle():
    async with webhook_api() as env:
        response = await signed_post(env.client, "diddipay", payment_event())
        assert response.status_code == 200, response.text
        assert response.json() == {"status": "processed"}
        assert await env.inbox.seen("diddishop-diddipay", "payment-event")
        saved = await env.orders.get("order")
        assert saved.fulfillment_status is FulfillmentStatus.TO_CONFIRM
        assert saved.payment_status is PaymentStatus.HELD
        assert saved.version == 1
        checkout = await env.client.get("/v1/checkouts/checkout")
        assert checkout.status_code == 200
        assert checkout.json()["status"] == "payment_succeeded"
        read = await env.client.get("/v1/orders/order")
        assert read.status_code == 200, read.text
        assert read.json()["payment_status"] == "HELD"
        listed = await env.client.get("/v1/orders")
        assert listed.status_code == 200
        assert listed.json()["items"][0]["fulfillment_status"] == "TO_CONFIRM"
        assert (await env.client.get("/v1/deliveries/orders/order")).status_code == 200
        replay = await signed_post(env.client, "diddipay", payment_event())
        assert replay.json() == {"status": "duplicate"}
        assert len(await env.outbox.pending()) == 1
        env.actor.value = Actor("seller", "user")
        shops = await env.client.get("/v1/shops/mine")
        assert shops.status_code == 200, shops.text
        assert shops.json()["items"][0]["status"] == "active"
        pending = await env.client.get("/v1/orders/seller/to-confirm")
        assert pending.status_code == 200
        assert [item["id"] for item in pending.json()["items"]] == ["order"]
        confirmed = await env.client.post("/v1/orders/order/confirm")
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["fulfillment_status"] == "TO_PREPARE"
        for _ in range(2):
            ready = await env.client.post("/v1/orders/order/ready")
            assert ready.status_code == 200, ready.text
            assert ready.json()["delivery_id"] == "delivery-test"
        assert len(env.sender.calls) == 1
        assert env.sender.calls[0][0].idempotency_key == "shop:create-delivery:order:1"
        for event_type in ("delivery.created", "delivery.picked_up", "delivery.in_transit", "delivery.delivered"):
            event = {
                "event_id": event_type, "event_type": event_type, "delivery_id": "delivery-test",
                "source_service": "diddisend",
                "occurred_at": "2026-11-27T13:00:00Z", "order_reference": "shop-order:order",
                "status": event_type.removeprefix("delivery."), "data": {},
            }
            result = await signed_post(env.client, "diddisend", event)
            assert result.status_code == 200, result.text
        order = await env.orders.get("order")
        assert order.fulfillment_status is FulfillmentStatus.DELIVERED
        assert order.payment_status is PaymentStatus.HELD
        assert order.metadata["delivered_at"]
        assert "release_eligible_at" not in order.metadata
        for principal in (Actor("buyer", "user"), Actor("seller", "user")):
            env.actor.value = principal
            delivery = await env.client.get("/v1/deliveries/orders/order")
            assert delivery.status_code == 200
            assert delivery.json()["status"] == "delivered"
        repeated = await signed_post(env.client, "diddisend", event)
        assert repeated.json() == {"status": "duplicate"}
        assert (await env.orders.get("order")).metadata["delivered_at"] == order.metadata["delivered_at"]


@pytest.mark.asyncio
async def test_failed_save_does_not_acknowledge_callback_and_same_event_can_recover(monkeypatch):
    async with webhook_api() as env:
        original_save = env.orders.save

        async def unavailable(_order):
            raise RuntimeError("simulated persistence failure")

        monkeypatch.setattr(env.orders, "save", unavailable)
        response = await signed_post(env.client, "diddipay", payment_event())
        assert response.status_code == 500
        assert not await env.inbox.seen("diddishop-diddipay", "payment-event")
        assert (await env.checkouts.get("checkout")).status is CheckoutStatus.PAYMENT_PENDING
        assert (await env.orders.get("order")).version == 0
        monkeypatch.setattr(env.orders, "save", original_save)
        retried = await signed_post(env.client, "diddipay", payment_event())
        assert retried.status_code == 200, retried.text
        assert (await env.orders.get("order")).payment_status is PaymentStatus.HELD
        assert len(await env.outbox.pending()) == 1


@pytest.mark.asyncio
async def test_sql_payment_transition_preserves_rewards_snapshot_and_avoids_reconsumption():
    async with webhook_api() as env:
        class RewardsAdapter:
            calls = 0

            async def confirm(self, payload, idempotency_key):
                self.calls += 1
                return {"consumption_id": "consumption-test"}

        adapter = RewardsAdapter()
        rewards = RewardsService(adapter)
        env.app.state.order_service.rewards = rewards
        order = await env.orders.get("order")
        order.metadata["rewards"] = rewards.to_metadata(RewardReservation(
            reservation_id="reservation", entitlement_id="entitlement", operation_id="operation",
            reserved_amount_minor=100,
            snapshot=CampaignSnapshot(campaign_id="campaign", campaign_version_id="version",
                                      entitlement_id="entitlement", discount_minor=100, final_amount_minor=5640),
        ))
        await env.orders.save(order)
        for event_id in ("payment-event", "another-event-for-same-success"):
            response = await signed_post(env.client, "diddipay", payment_event(event_id))
            assert response.status_code == 200, response.text
        saved = await env.orders.get("order")
        assert saved.metadata["rewards"]["consumption_id"] == "consumption-test"
        assert saved.payment_status is PaymentStatus.HELD
        assert saved.version == 1
        assert adapter.calls == 1


@pytest.mark.asyncio
async def test_read_routes_preserve_authorization_and_missing_order_404():
    async with webhook_api() as env:
        env.actor.value = Actor("outsider", "user")
        for path in ("/v1/orders/order", "/v1/deliveries/orders/order"):
            response = await env.client.get(path)
            assert response.status_code == 403, response.text
        for path in ("/v1/orders/order/confirm", "/v1/orders/order/ready"):
            assert (await env.client.post(path)).status_code == 403
        assert (await env.client.get("/v1/orders/missing")).status_code == 404
        env.actor.value = Actor("buyer", "user")
        assert (await env.client.post("/v1/orders/order/confirm")).status_code == 403
        assert not env.sender.calls


@pytest.mark.asyncio
async def test_invalid_signature_does_not_mutate_or_acknowledge_event():
    async with webhook_api() as env:
        response = await signed_post(env.client, "diddipay", payment_event(), secret="wrong")
        assert response.status_code == 401
        assert not await env.inbox.seen("diddishop-diddipay", "payment-event")
        assert (await env.orders.get("order")).version == 0
        assert (await env.checkouts.get("checkout")).status is CheckoutStatus.PAYMENT_PENDING


@pytest.mark.asyncio
async def test_multishop_partial_failure_recovers_without_repeating_completed_transition(monkeypatch):
    async with webhook_api() as env:
        await env.orders.create(Order("order-2", "shop", "checkout", 1000))
        checkout = await env.checkouts.get("checkout")
        checkout.order_ids.append("order-2")
        checkout.total_minor += 1000
        await env.checkouts.save(checkout)
        original_save = env.orders.save

        async def unavailable_second_order(order):
            if order.id == "order-2":
                raise RuntimeError("simulated second-order failure")
            await original_save(order)

        monkeypatch.setattr(env.orders, "save", unavailable_second_order)
        event = payment_event()
        event["data"]["amount"] = 6640
        response = await signed_post(env.client, "diddipay", event)
        assert response.status_code == 500
        assert not await env.inbox.seen("diddishop-diddipay", "payment-event")
        assert (await env.orders.get("order")).payment_status is PaymentStatus.HELD
        assert (await env.orders.get("order-2")).fulfillment_status is FulfillmentStatus.PAYMENT_PENDING
        monkeypatch.setattr(env.orders, "save", original_save)
        assert (await signed_post(env.client, "diddipay", event)).status_code == 200
        for order_id in checkout.order_ids:
            saved = await env.orders.get(order_id)
            assert saved.fulfillment_status is FulfillmentStatus.TO_CONFIRM
            assert saved.payment_status is PaymentStatus.HELD
            assert saved.version == 1
        assert (await env.checkouts.get("checkout")).status is CheckoutStatus.PAYMENT_SUCCEEDED
        assert len(await env.outbox.pending()) == 2


@pytest.mark.parametrize("fulfillment", list(FulfillmentStatus))
@pytest.mark.parametrize("payment", list(PaymentStatus))
def test_order_json_status_values_restore_known_enums(fulfillment, payment):
    order = Order("order", "shop", "checkout", 1500,
                  fulfillment_status=fulfillment.value, payment_status=payment.value)
    assert order.fulfillment_status is fulfillment
    assert order.payment_status is payment


@pytest.mark.parametrize("field", ["payment_status", "fulfillment_status"])
def test_unknown_persisted_status_is_not_replaced_by_a_default(field):
    with pytest.raises(ValueError):
        Order("order", "shop", "checkout", 1500, **{field: "unexpected"})


@pytest.mark.asyncio
async def test_sql_shop_order_and_delivery_statuses_are_rehydrated_on_get_and_list():
    async with webhook_api() as env:
        shop = await env.shops.get("shop")
        assert shop.status is ShopStatus.ACTIVE
        assert (await env.shops.list_for_owner("seller"))[0].status is ShopStatus.ACTIVE
        await env.shops.save(shop)
        for order in (await env.orders.get("order"), (await env.orders.list_for_shop("shop"))[0]):
            assert order.fulfillment_status is FulfillmentStatus.PAYMENT_PENDING
            assert order.payment_status is PaymentStatus.PENDING
            await env.orders.save(order)
        await env.deliveries.save(DeliveryProjection("delivery-test", "order", DeliveryStatus.REQUESTED))
        delivery = await env.deliveries.get_by_order("order")
        assert delivery.status is DeliveryStatus.REQUESTED
        await env.deliveries.save(delivery)
