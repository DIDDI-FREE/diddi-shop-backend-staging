from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from app_base.core.api_contracts import CheckoutQuoteResponse, CheckoutResponse, checkout_response
from app_base.core.auth_deps import Actor, current_actor
from app_base.core.idempotency import IdempotencyRecord, replay_or_none, request_hash
from app_base.core.observability import log_event
from app_base.modules.checkout.application.checkout_service import CheckoutApplicationService
from app_base.modules.checkout.presentation import CheckoutQuoteRequest, CreateCheckoutRequest

router = APIRouter(prefix="/v1/checkouts", tags=["checkout"])

IDEMPOTENT_RESPONSE = {
    200: {"headers": {"Idempotency-Replayed": {
        "description": "true = stored response, no new DiddiPay call; false = new attempt",
        "schema": {"type": "string", "enum": ["true", "false"]},
    }}},
}


def checkout_service(request: Request) -> CheckoutApplicationService:
    return request.app.state.checkout_service


@router.post("", response_model=CheckoutResponse, responses=IDEMPOTENT_RESPONSE)
async def create_checkout(
    body: CreateCheckoutRequest,
    request: Request,
    http_response: Response,
    actor: Actor = Depends(current_actor),
    service: CheckoutApplicationService = Depends(checkout_service),
):
    store = request.app.state.idempotency_store_factory("checkout")
    request_body = {"customer_id": actor.subject, **body.model_dump()}
    previous = await replay_or_none(store, body.idempotency_key, request_body)
    http_response.headers["Idempotency-Replayed"] = str(previous is not None).lower()
    if previous is not None:
        log_event("checkout.create.replayed", checkout_id=previous.response_body.get("id"))
        return previous.response_body
    context = _delivery_context(body)
    checkout = await service.create(actor.subject, body.idempotency_key, context or None)
    response = checkout_response(checkout, checkout.payment)
    await store.save(IdempotencyRecord(
        key=body.idempotency_key,
        request_hash=request_hash(request_body),
        status_code=200,
        response_body=response,
    ))
    return response


def _delivery_context(body: CreateCheckoutRequest | CheckoutQuoteRequest) -> dict:
    context = body.model_dump(exclude_none=True)
    context.pop("idempotency_key", None)
    context["dropoff_location"] = {
        "lat": context.pop("dropoff_latitude"),
        "lng": context.pop("dropoff_longitude"),
        "address": context.pop("dropoff_address"),
    }
    return context


@router.post("/quote", response_model=CheckoutQuoteResponse)
async def quote_checkout(
    body: CheckoutQuoteRequest,
    actor: Actor = Depends(current_actor),
    service: CheckoutApplicationService = Depends(checkout_service),
):
    return await service.quote(actor.subject, _delivery_context(body))


@router.get("/{checkout_id}", response_model=CheckoutResponse)
async def get_checkout(
    checkout_id: str,
    actor: Actor = Depends(current_actor),
    service: CheckoutApplicationService = Depends(checkout_service),
):
    checkout = await service.get(checkout_id)
    if checkout.customer_id != actor.subject and actor.actor_type not in {"admin", "support", "service"}:
        raise HTTPException(status_code=403, detail="checkout access denied")
    return checkout_response(checkout, checkout.payment)


@router.post(
    "/{checkout_id}/retry", response_model=CheckoutResponse,
    responses={
        **IDEMPOTENT_RESPONSE,
        422: {
            "description": "PAYMENT_PHONE_REQUIRED: no valid persisted phone; no attempt started",
            "content": {"application/json": {"schema": {
                "type": "object", "required": ["error", "message"],
                "properties": {"error": {"type": "string"}, "message": {"type": "string"}},
            }}},
        },
    },
)
async def retry_checkout_payment(
    checkout_id: str,
    request: Request,
    http_response: Response,
    actor: Actor = Depends(current_actor),
    service: CheckoutApplicationService = Depends(checkout_service),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    current = await service.get(checkout_id)
    if current.customer_id != actor.subject and actor.actor_type not in {"admin", "support", "service"}:
        raise HTTPException(status_code=403, detail="checkout access denied")
    store = request.app.state.idempotency_store_factory("checkout-payment-retry")
    request_body = {"checkout_id": checkout_id, "customer_id": actor.subject}
    previous = await replay_or_none(store, idempotency_key, request_body)
    http_response.headers["Idempotency-Replayed"] = str(previous is not None).lower()
    if previous is not None:
        log_event(
            "checkout.payment.replayed", checkout_id=checkout_id,
            attempt=previous.response_body.get("payment_attempt"),
        )
        return previous.response_body
    checkout = await service.retry_payment(checkout_id, idempotency_key)
    response = checkout_response(checkout, checkout.payment)
    await store.save(IdempotencyRecord(
        key=idempotency_key,
        request_hash=request_hash(request_body),
        status_code=200,
        response_body=response,
    ))
    return response
