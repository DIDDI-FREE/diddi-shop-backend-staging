"""Exercise actual HTTP routes, SQL persistence and DiddiPay wire payloads."""

import json
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app_base.core.api_contracts import checkout_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.core.business_repositories import (
    SqlCartRepository,
    SqlCheckoutRepository,
    SqlOrderRepository,
    SqlProductRepository,
)
from app_base.core.durable_stores import SqlIdempotencyStore
from app_base.core.errors import DiddiShopError, PaymentPhoneRequiredError
from app_base.core.idempotency import IdempotencyRecord, request_hash
from app_base.core.platform_models import Base
from app_base.integrations.auth import ServiceCredential
from app_base.integrations.checkout_ports import DiddiPayPaymentIntentPort
from app_base.integrations.diddipay import DiddiPayAdapter
from app_base.main import handle_domain_error, handle_validation_error
from app_base.modules.cart.domain import CartLine
from app_base.modules.catalog.domain import Product, ProductStatus
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.domain import Checkout, CheckoutStatus
from app_base.modules.checkout.return_router import router as return_router
from app_base.modules.checkout.router import router
from app_base.modules.orders.domain.entities import Order
from app_base.shared_kernel.contracts.payments import (
    DEFAULT_PAYMENT_RETURN_URL,
    PaymentIntentCommand,
)

PHONE = "+2250700000000"  # Synthetic fixture; never used against a real provider.
RETURN_URL = "https://app.diddifree.com/payment/complete"


@asynccontextmanager
async def payment_api(*, redirect=False):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    requests = []

    async def pay_handler(request):
        requests.append(request)
        payload = json.loads(request.content)
        if not payload.get("customer_phone"):
            return httpx.Response(201, json={
                "id": str(uuid4()), "status": "failed",
                "failure_code": "PROCESSOR_REQUEST_REJECTED",
                "failure_message": "customer_phone is required by pawapay deposits",
                "provider_status": "rejected_before_call",
            })
        if not payload.get("callback_url") and not payload.get("return_target"):
            return httpx.Response(201, json={
                "id": str(uuid4()), "status": "failed",
                "failure_code": "PROCESSOR_REQUEST_REJECTED",
                "failure_message": "callback_url is required by pawapay's Payment Page (used as returnUrl)",
            })
        if payload.get("return_target") == "unconfigured":
            return httpx.Response(422, json={"error": {"code": "PAYMENT_RETURN_TARGET_FORBIDDEN"}})
        if redirect:
            return httpx.Response(201, json={
                "id": str(uuid4()), "status": "requires_action", "provider_status": "page_created",
                "next_action": {"type": "redirect", "url": "https://payment.example/session/test",
                                "expires_at": "2026-12-01T12:00:00Z"},
            })
        # DiddiPay need not echo inputs. A nullable response must not erase them.
        return httpx.Response(201, json={
            "id": str(uuid4()), "status": "failed", "customer_phone": None, "return_url": None,
            "failure_code": "TEST_DECLINED", "failure_message": "Simulated decline",
        })

    adapter = DiddiPayAdapter(
        base_url="https://pay.test/payfund/v1", audience="diddipay",
        credential=ServiceCredential(service="diddipay", client_id="test-shop", access_token="test"),
        transport=httpx.MockTransport(pay_handler),
    )

    class Quote:
        async def quote(self, *args):
            return 4140

    service = CheckoutApplicationService(
        SqlCartRepository(factory), SqlProductRepository(factory),
        SqlCheckoutRepository(factory), SqlOrderRepository(factory),
        Quote(), DiddiPayPaymentIntentPort(adapter), [],
    )
    await service.products.save(Product(
        "product", "shop", "Article", "", 1500, "XOF", 3, "books", [], ProductStatus.PUBLISHED,
    ))
    cart = await service.carts.get_or_create("buyer")
    cart.lines = [CartLine("product", "shop", 1)]
    await service.carts.save(cart)
    app = FastAPI()
    app.include_router(router)
    app.include_router(return_router)
    app.add_exception_handler(DiddiShopError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.dependency_overrides[current_actor] = lambda: Actor("buyer", "user")
    app.state.checkout_service = service
    app.state.idempotency_store_factory = lambda scope: SqlIdempotencyStore(factory, scope)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="https://shop.test",
        ) as client:
            yield client, service, requests
    finally:
        await engine.dispose()


def checkout_body(method="orange_money"):
    return {
        "idempotency_key": "create-1", "recipient_name": "Test buyer",
        "recipient_phone": PHONE, "dropoff_address": "Test address",
        "dropoff_latitude": 5.34, "dropoff_longitude": -4.03,
        "payment_method": method, "return_url": RETURN_URL,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("method,network", [("orange_money", "orange"), ("mtn_momo", "mtn"), ("wave", "wave")])
async def test_create_read_and_retry_send_phone_through_real_adapter_and_sql(method, network):
    async with payment_api() as (client, service, sent):
        created = await client.post("/v1/checkouts", json=checkout_body(method))
        assert created.status_code == 200
        checkout_id = created.json()["id"]
        assert created.json()["status"] == "payment_failed"
        assert created.json()["payment"]["payment_failure_code"] == "TEST_DECLINED"
        assert json.loads(sent[0].content)["customer_phone"] == PHONE
        persisted = await service.checkouts.get(checkout_id)
        assert persisted.payment["customer_phone"] == PHONE
        read = await client.get(f"/v1/checkouts/{checkout_id}")
        assert read.status_code == 200
        retry = await client.post(f"/v1/checkouts/{checkout_id}/retry", headers={"Idempotency-Key": "retry-2"})
        assert retry.status_code == 200
        assert retry.json()["payment_attempt"] == 2
        assert len(sent) == 2
        for request in sent:
            body = json.loads(request.content)
            assert request.url.path == "/payfund/v1/payment-intents"
            assert body["customer_phone"] == PHONE
            assert body["channel"] == "mobile_money"
            assert body["network"] == network
            assert body["amount"] == 5640
            assert body["currency"] == "XOF"
            assert "recipient_phone" not in body
        assert sent[1].headers["idempotency-key"] == "retry-2"
        assert (await service.products.get("product")).stock == 2
        assert PHONE not in retry.text


async def legacy_checkout(service, phone, stored_phone=None, return_url=RETURN_URL):
    order = Order("old-order", "shop", "old-checkout", 5640,
                  metadata={"delivery_request": {"recipient_phone": phone, "return_url": return_url}})
    await service.orders.create(order)
    checkout = Checkout(
        "old-checkout", "buyer", 5640, "XOF", [order.id],
        status=CheckoutStatus.PAYMENT_FAILED,
        payment={"status": "failed", "payment_method": "orange_money", "customer_phone": stored_phone},
        payment_idempotency_key="old-key",
    )
    await service.checkouts.save(checkout)
    return checkout


@pytest.mark.asyncio
@pytest.mark.parametrize("stored_phone", [None, "unknown", " "])
async def test_legacy_retry_recovers_valid_phone_from_sql_order(stored_phone):
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE, stored_phone)
        response = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "retry-2"})
        assert response.status_code == 200
        assert len(sent) == 1
        assert json.loads(sent[0].content)["customer_phone"] == PHONE


@pytest.mark.asyncio
@pytest.mark.parametrize("phone", [None, "", "unknown", " ", "not-a-phone"])
async def test_legacy_retry_without_valid_phone_is_blocked_before_call_or_attempt_change(phone):
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, phone)
        response = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "retry-2"})
        assert response.status_code == 422
        assert response.json()["error"] == "PAYMENT_PHONE_REQUIRED"
        assert not sent
        saved = await service.checkouts.get(checkout.id)
        assert saved.status == CheckoutStatus.PAYMENT_FAILED
        assert saved.payment_attempt == 1
        assert saved.payment_idempotency_key == "old-key"


@pytest.mark.asyncio
async def test_return_url_is_mapped_persisted_and_reused_on_retry():
    async with payment_api() as (client, service, sent):
        created = await client.post("/v1/checkouts", json=checkout_body())
        assert created.status_code == 200
        assert json.loads(sent[0].content)["callback_url"] == RETURN_URL
        checkout = await service.checkouts.get(created.json()["id"])
        assert checkout.payment["return_url"] == RETURN_URL
        retried = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "retry-return"})
        assert retried.status_code == 200
        assert json.loads(sent[-1].content)["callback_url"] == RETURN_URL
        assert "return_url" not in json.loads(sent[-1].content)


@pytest.mark.asyncio
async def test_retry_can_repair_missing_historical_return_with_idempotent_optional_body():
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE, return_url=None)
        url = f"/v1/checkouts/{checkout.id}/retry"
        first = await client.post(url, headers={"Idempotency-Key": "return-fix"}, json={"return_target": "app"})
        assert first.status_code == 200
        assert json.loads(sent[0].content)["return_target"] == "app"
        assert "callback_url" not in json.loads(sent[0].content)
        replay = await client.post(url, headers={"Idempotency-Key": "return-fix"}, json={"return_target": "app"})
        assert replay.headers["Idempotency-Replayed"] == "true"
        conflict = await client.post(url, headers={"Idempotency-Key": "return-fix"}, json={"return_target": "web"})
        assert conflict.status_code == 409
        assert len(sent) == 1
        followup = await client.post(url, headers={"Idempotency-Key": "return-fix-2"})
        assert followup.status_code == 200
        assert json.loads(sent[-1].content)["return_target"] == "app"


@pytest.mark.asyncio
async def test_missing_return_blocks_creation_and_retry_before_side_effects():
    async with payment_api() as (client, service, sent):
        service.payment_return_url = None
        body = checkout_body()
        body.pop("return_url")
        created = await client.post("/v1/checkouts", json=body)
        assert created.status_code == 422
        assert created.json()["error"] == "PAYMENT_RETURN_REQUIRED"
        assert not await service.orders.list_for_shop("shop")
        assert (await service.products.get("product")).stock == 3
        checkout = await legacy_checkout(service, PHONE, return_url=None)
        retry = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "missing-return"})
        assert retry.status_code == 422
        assert retry.json()["error"] == "PAYMENT_RETURN_REQUIRED"
        assert not sent
        saved = await service.checkouts.get(checkout.id)
        assert saved.payment_attempt == 1
        assert saved.status == CheckoutStatus.PAYMENT_FAILED
        assert saved.payment_idempotency_key == "old-key"


@pytest.mark.asyncio
async def test_payment_page_redirect_reaches_frontend_without_marking_checkout_paid():
    async with payment_api(redirect=True) as (client, _service, sent):
        body = checkout_body()
        body.pop("return_url")
        body["return_target"] = "app"
        response = await client.post("/v1/checkouts", json=body)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "payment_pending"
        assert result["payment"]["next_action"]["type"] == "redirect"
        assert result["payment"]["payment_url"] == "https://payment.example/session/test"
        assert json.loads(sent[0].content)["return_target"] == "app"
        read = await client.get(f"/v1/checkouts/{result['id']}")
        assert read.json()["payment"]["next_action"] == result["payment"]["next_action"]


@pytest.mark.asyncio
async def test_upstream_refused_return_target_stays_failed_and_can_be_corrected():
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE)
        url = f"/v1/checkouts/{checkout.id}/retry"
        refused = await client.post(url, headers={"Idempotency-Key": "bad-target"}, json={"return_target": "unconfigured"})
        assert refused.status_code == 200
        assert refused.json()["status"] == "payment_failed"
        assert refused.json()["payment"]["payment_failure_code"] == "PAYMENT_RETURN_TARGET_FORBIDDEN"
        corrected = await client.post(url, headers={"Idempotency-Key": "good-target"}, json={"return_url": RETURN_URL})
        assert corrected.status_code == 200
        assert corrected.json()["payment_attempt"] == 3
        assert json.loads(sent[-1].content)["callback_url"] == RETURN_URL
        assert "return_target" not in json.loads(sent[-1].content)
        saved = await service.checkouts.get(checkout.id)
        assert saved.status == CheckoutStatus.PAYMENT_FAILED
        assert saved.payment_attempt == 3
        assert saved.payment_idempotency_key == "good-target"


@pytest.mark.asyncio
async def test_default_return_covers_new_and_historical_checkouts_without_frontend_change():
    async with payment_api() as (client, service, sent):
        body = checkout_body()
        body.pop("return_url")
        response = await client.post("/v1/checkouts", json=body)
        assert response.status_code == 200
        assert json.loads(sent[-1].content)["callback_url"] == DEFAULT_PAYMENT_RETURN_URL
        checkout = await legacy_checkout(service, PHONE, return_url=None)
        response = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "default-return"})
        assert response.status_code == 200
        assert json.loads(sent[-1].content)["callback_url"] == DEFAULT_PAYMENT_RETURN_URL


@pytest.mark.asyncio
async def test_configured_target_takes_precedence_over_default_url():
    async with payment_api() as (client, service, sent):
        service.payment_return_target = "app"
        body = checkout_body()
        body.pop("return_url")
        response = await client.post("/v1/checkouts", json=body)
        assert response.status_code == 200
        wire = json.loads(sent[-1].content)
        assert wire["return_target"] == "app"
        assert "callback_url" not in wire


@pytest.mark.asyncio
@pytest.mark.parametrize("options", [
    {"return_url": "http://app.diddifree.com/return"},
    {"return_url": "https://localhost/return"},
    {"return_url": "https://diddifree.com.evil.test/return"},
    {"return_url": "https://user:pass@app.diddifree.com/return"},
    {"return_url": "https://app.diddifree.com/%2e%2e/return"},
    {"return_url": "https://app.diddifree.com/return%0d%0a"},
    {"return_url": RETURN_URL, "return_target": "app"},
    {"return_target": ""},
])
async def test_invalid_return_rejected_with_serializable_422_before_effects(options):
    async with payment_api() as (client, service, sent):
        body = checkout_body()
        body.pop("return_url")
        body.update(options)
        response = await client.post("/v1/checkouts", json=body)
        assert response.status_code == 422
        assert response.json()["error"] == "VALIDATION_ERROR"
        assert not await service.orders.list_for_shop("shop")
        checkout = await legacy_checkout(service, PHONE)
        response = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "bad-return"}, json=options)
        assert response.status_code == 422
        assert (await service.checkouts.get(checkout.id)).payment_attempt == 1
        assert not sent


@pytest.mark.asyncio
async def test_browser_return_is_public_and_never_confirms_or_reflects_query_parameters():
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE)
        app = client._transport.app
        app.dependency_overrides.clear()
        response = await client.get("/payments/return?status=paid&reference=SECRET&redirect=https://evil.test")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "no-store"
        assert "SECRET" not in response.text and "evil.test" not in response.text
        assert "Location" not in response.headers
        assert "ne confirme pas le paiement" in response.text
        assert (await service.checkouts.get(checkout.id)).status == CheckoutStatus.PAYMENT_FAILED
        assert not sent


@pytest.mark.asyncio
async def test_retry_same_key_reports_replay_without_new_payment_and_new_key_really_calls():
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE)
        url = f"/v1/checkouts/{checkout.id}/retry"
        first = await client.post(url, headers={"Idempotency-Key": "retry-2"})
        assert first.status_code == 200
        assert first.headers["Idempotency-Replayed"] == "false"
        replay = await client.post(url, headers={"Idempotency-Key": "retry-2"})
        assert replay.status_code == 200
        assert replay.headers["Idempotency-Replayed"] == "true"
        assert replay.json() == first.json()
        assert len(sent) == 1
        new = await client.post(url, headers={"Idempotency-Key": "retry-3"})
        assert new.status_code == 200
        assert new.headers["Idempotency-Replayed"] == "false"
        assert new.json()["payment_attempt"] == 3
        assert len(sent) == 2


@pytest.mark.asyncio
async def test_old_cached_failure_is_identified_not_recharged_until_new_key(caplog):
    async with payment_api() as (client, service, sent):
        checkout = await legacy_checkout(service, PHONE)
        checkout.payment_attempt = 2
        checkout.payment_idempotency_key = "historical-retry"
        checkout.payment.update({
            "failure_code": "PROCESSOR_REQUEST_REJECTED",
            "failure_message": "customer_phone is required by pawapay deposits",
        })
        await service.checkouts.save(checkout)
        old_response = checkout_response(checkout, checkout.payment)
        store = client._transport.app.state.idempotency_store_factory("checkout-payment-retry")
        await store.save(IdempotencyRecord(
            "historical-retry", request_hash({"checkout_id": checkout.id, "customer_id": "buyer"}),
            200, old_response,
        ))
        with caplog.at_level("INFO", logger="diddi_shop"):
            replay = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "historical-retry"})
            assert replay.status_code == 200
            assert replay.headers["Idempotency-Replayed"] == "true"
            assert replay.json()["payment_attempt"] == 2
            assert not sent
            fresh = await client.post(f"/v1/checkouts/{checkout.id}/retry", headers={"Idempotency-Key": "fresh-retry"})
        assert fresh.status_code == 200
        assert fresh.headers["Idempotency-Replayed"] == "false"
        assert fresh.json()["payment_attempt"] == 3
        assert len(sent) == 1
        assert json.loads(sent[0].content)["customer_phone"] == PHONE
        assert "checkout.payment.replayed" in caplog.text
        assert "checkout.payment.intent_requested" in caplog.text
        assert PHONE not in caplog.text
        assert "historical-retry" not in caplog.text


@pytest.mark.asyncio
async def test_create_replay_does_not_reserve_stock_or_charge_again():
    async with payment_api() as (client, service, sent):
        first = await client.post("/v1/checkouts", json=checkout_body())
        second = await client.post("/v1/checkouts", json=checkout_body())
        assert first.headers["Idempotency-Replayed"] == "false"
        assert second.headers["Idempotency-Replayed"] == "true"
        assert first.json() == second.json()
        assert len(sent) == 1
        assert (await service.products.get("product")).stock == 2


@pytest.mark.asyncio
async def test_application_refuses_missing_phone_before_stock_order_or_payment():
    async with payment_api() as (_, service, sent):
        with pytest.raises(PaymentPhoneRequiredError):
            await service.create("buyer", "missing-phone", {})
        assert not sent
        assert not await service.orders.list_for_shop("shop")
        assert not await service.checkouts.list_for_customer("buyer")
        assert (await service.products.get("product")).stock == 3


@pytest.mark.asyncio
async def test_real_payment_port_and_adapter_fail_closed_without_valid_phone():
    async with payment_api() as (_, service, sent):
        with pytest.raises(PaymentPhoneRequiredError):
            await service.payments.create("checkout", 5640, "legacy-call")
        # Even an internal caller bypassing Pydantic must not send an empty phone.
        command = PaymentIntentCommand.model_construct(
            checkout_id="checkout", business_reference="diddishop:checkout:checkout",
            amount_minor=5640, idempotency_key="bad-input", customer_phone=None,
        )
        with pytest.raises(PaymentPhoneRequiredError):
            await service.payments.adapter.create_payment_intent(command)
        assert not sent
