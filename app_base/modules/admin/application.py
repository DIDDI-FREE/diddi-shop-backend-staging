from app_base.core.errors import ConflictError


class AdminService:
    def __init__(self, orders, claims, finance, audit, deliveries):
        self.orders = orders
        self.claims = claims
        self.finance = finance
        self.audit = audit
        self.deliveries = deliveries

    async def read_order(self, order_id: str, actor: str) -> dict:
        order = await self.orders.get(order_id)
        delivery = await self.deliveries.get_by_order(order_id)
        await self.audit.append("admin.read_order", actor, order_id, {"source": "diddishop"})
        return {"order": order, "delivery_projection": delivery}

    async def decide_claim(self, claim_id: str, decision, amount_to_refund: int, actor: str, reason: str) -> object:
        if not reason.strip():
            raise ConflictError("admin reason is required")
        result = await self.finance.decide(claim_id, decision, amount_to_refund)
        await self.audit.append("admin.decide_claim", actor, claim_id, {"decision": str(decision), "reason": reason})
        return result
