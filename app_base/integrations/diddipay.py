from app_base.core.observability import log_event
from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.payments import (
    PaymentIntentCommand,
    require_customer_phone,
    require_payment_return,
)

RETURN_REJECTION_CODES = {
    "PAYMENT_RETURN_TARGET_CONFLICT", "PAYMENT_RETURN_TARGET_FORBIDDEN",
    "PAYMENT_CALLBACK_URL_DISABLED", "PAYMENT_CALLBACK_URL_FORBIDDEN",
}


class DiddiPayAdapter(ServiceAdapter):
    async def create_payment_intent(self, command: PaymentIntentCommand) -> dict:
        network_by_method = {
            "wave": "wave",
            "mtn_momo": "mtn",
            "orange_money": "orange",
        }
        request_payload = {
            "business_reference": command.business_reference,
            "amount": command.amount_minor,
            "currency": command.currency,
            "channel": "mobile_money",
            "network": network_by_method[command.payment_method],
            "customer_phone": require_customer_phone(command.customer_phone),
            "metadata": {"checkout_id": command.checkout_id, "origin_service": "diddishop"},
        }
        destination = require_payment_return(command.return_url, command.return_target)
        if destination.return_target:
            request_payload["return_target"] = destination.return_target
        else:
            request_payload["callback_url"] = destination.return_url
        log_event(
            "checkout.payment.intent_requested", checkout_id=command.checkout_id,
            network=request_payload["network"], customer_contact_present=True,
            return_mode="target" if destination.return_target else "url",
        )
        response = await self.request(
            "POST", "/payment-intents",
            headers={"Idempotency-Key": command.idempotency_key},
            json=request_payload,
        )
        # Only explicit pre-payment validation rejections are safe to retry.
        # Transport/5xx failures remain ambiguous and must not be labelled failed.
        if response.status_code == 422:
            error = response.json().get("error", {})
            code = error.get("code") if isinstance(error, dict) else error
            if code in RETURN_REJECTION_CODES:
                log_event("checkout.payment.return_rejected", checkout_id=command.checkout_id, code=code)
                return {
                    "payment_intent_id": None, "status": "failed", "failure_code": code,
                    "failure_message": "DiddiPay refused the configured browser return destination",
                    "provider_status": "rejected_by_diddipay",
                }
        response.raise_for_status()
        payload = response.json()
        if "payment_intent_id" not in payload and payload.get("id"):
            payload["payment_intent_id"] = payload["id"]
        if "amount_minor" not in payload and payload.get("amount") is not None:
            payload["amount_minor"] = payload["amount"]
        action = payload.get("next_action")
        if isinstance(action, dict):
            payload["next_action"] = {
                key: action[key] for key in ("type", "url", "instructions", "expires_at") if key in action
            }
            if action.get("type") == "redirect" and action.get("url"):
                payload["payment_url"] = action["url"]
            if action.get("expires_at"):
                payload["expires_at"] = action["expires_at"]
        log_event(
            "checkout.payment.intent_resolved", checkout_id=command.checkout_id,
            intent_id=payload.get("payment_intent_id"), status=payload.get("status"),
        )
        return payload

    async def refund(self, order_id: str, amount_minor: int, idempotency_key: str) -> dict:
        response = await self.request(
            "POST", f"/payment-intents/{order_id}/refunds",
            headers={"Idempotency-Key": idempotency_key},
            json={
                "amount": amount_minor,
                "reason": "diddishop_order",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if "refund_id" not in payload and payload.get("id"):
            payload["refund_id"] = payload["id"]
        return payload

    async def cancel_payment_intent(self, payment_intent_id: str, idempotency_key: str) -> dict:
        response = await self.request(
            "POST",
            f"/payment-intents/{payment_intent_id}/cancel",
            headers={"Idempotency-Key": idempotency_key},
            json={"reason": "order_expired"},
        )
        response.raise_for_status()
        return response.json()

    async def request_release(self, order_id: str, amount_minor: int, idempotency_key: str) -> dict:
        raise NotImplementedError("Marketplace seller release must be added to the DiddiPay contract")

    async def release(self, order_id: str, amount_minor: int, idempotency_key: str) -> None:
        await self.request_release(order_id, amount_minor, idempotency_key)
