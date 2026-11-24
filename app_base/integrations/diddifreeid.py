from app_base.integrations.auth import ServiceTokenProvider
from app_base.integrations.base import ServiceAdapter


class DiddiFreeIDAdapter(ServiceAdapter):
    """Token acquisition stays behind this adapter; no JWT logic in domain code."""

    async def issue_service_token(
        self,
        audience: str,
        scope: str,
        *,
        client_id: str,
        client_secret: str,
    ) -> str:
        """Issue one target-scoped token using DiddiFreeID's service contract."""
        provider = ServiceTokenProvider(
            token_url=self._url("/identity/v1/auth/service/token"),
            client_id=client_id,
            client_secret=client_secret,
            audience=audience,
            scopes=tuple(scope.split()),
            timeout_seconds=self.timeout,
        )
        return await provider.access_token()
