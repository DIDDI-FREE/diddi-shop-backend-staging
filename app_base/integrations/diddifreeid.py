from app_base.integrations.base import ServiceAdapter


class DiddiFreeIDAdapter(ServiceAdapter):
    """Token acquisition stays behind this adapter; no JWT logic in domain code."""

    async def issue_service_token(self, audience: str, scope: str) -> str:
        raise NotImplementedError("Provision DiddiFreeID service credentials before enabling S2S calls")
