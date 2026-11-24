class SupportContextService:
    def __init__(self, orders, deliveries, claims):
        self.orders = orders
        self.deliveries = deliveries
        self.claims = claims

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
