from app_base.core.observability import log_event
from app_base.integrations.base import ServiceAdapter
from app_base.shared_kernel.contracts.payments import PaymentIntentCommand, require_customer_phone


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
        log_event(
            "checkout.payment.intent_requested", checkout_id=command.checkout_id,
            network=request_payload["network"], customer_contact_present=True,
        )
        response = await self.request(
            "POST", "/payment-intents",
            headers={"Idempotency-Key": command.idempotency_key},
            json=request_payload,
        )
        response.raise_for_status()
        payload = response.json()
        if "payment_intent_id" not in payload and payload.get("id"):
            payload["payment_intent_id"] = payload["id"]
        if "amount_minor" not in payload and payload.get("amount") is not None:
            payload["amount_minor"] = payload["amount"]
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
