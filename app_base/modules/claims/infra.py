from app_base.modules.claims.domain import Claim


class InMemoryClaimRepository:
    def __init__(self):
        self.items: dict[str, Claim] = {}

    async def save(self, claim: Claim) -> None:
        self.items[claim.id] = claim

    async def get(self, claim_id: str) -> Claim | None:
        return self.items.get(claim_id)

    async def get_open_for_order(self, order_id: str) -> Claim | None:
        return next((c for c in self.items.values() if c.order_id == order_id and c.status.value == "open"), None)
