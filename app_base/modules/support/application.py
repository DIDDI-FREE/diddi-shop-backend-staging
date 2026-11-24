class SupportContextService:
    def __init__(self, orders, deliveries, claims, adapter=None):
        self.orders = orders
        self.deliveries = deliveries
        self.claims = claims
        self.adapter = adapter

    async def build_order_context(self, order_id: str) -> dict:
        order = await self.orders.get(order_id)
        delivery = await self.deliveries.get_by_order(order_id)
        claim = await self.claims.get_open_for_order(order_id)
        return {
            "order": order,
            "delivery": delivery,
            "claim": claim,
            "owner_service": "diddishop",
            "source_of_truth": {"delivery": "diddisend", "payment": "diddipay", "files": "diddifiles"},
        }

    async def open_case(self, order_id: str, reporter_user_id: str, reason: str) -> dict:
        if self.adapter is None:
            raise RuntimeError("DiddiSupport adapter is not configured")
        return await self.adapter.create_case(
            {
                "origin_service": "diddishop",
                "resource_type": "order",
                "resource_id": order_id,
                "origin_report_id": f"diddishop:claim:{order_id}",
                "reporter_user_id": reporter_user_id,
                "category": "order_claim",
                "subject": reason,
                "priority": "normal",
            },
            f"shop:claim-case:{order_id}:1",
        )
