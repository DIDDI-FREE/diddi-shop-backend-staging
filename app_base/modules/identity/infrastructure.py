from app_base.core.errors import NotConfiguredError
from app_base.modules.identity.domain import Principal


class DiddiFreeIDTokenVerifier:
    """Fail-closed verifier seam; JWKS discovery is configured per environment."""

    def __init__(self, *, issuer: str | None = None, jwks_url: str | None = None):
        self.issuer = issuer
        self.jwks_url = jwks_url

    async def verify_user_token(self, token: str) -> Principal:
        if not self.issuer or not self.jwks_url:
            raise NotConfiguredError("DiddiFreeID JWKS verification is not configured")
        raise NotImplementedError("Wire JWKS validation against the provisioned DiddiFreeID issuer")

    async def verify_service_token(self, token: str, audience: str, scopes: set[str]) -> Principal:
        if not self.issuer or not self.jwks_url:
            raise NotConfiguredError("DiddiFreeID service-token verification is not configured")
        raise NotImplementedError("Wire JWKS validation against the provisioned DiddiFreeID issuer")
