from app_base.modules.identity.domain import Principal, TokenVerifier


class IdentityService:
    def __init__(self, verifier: TokenVerifier):
        self.verifier = verifier

    async def user(self, token: str) -> Principal:
        return await self.verifier.verify_user_token(token)

    async def service(self, token: str, audience: str, scopes: set[str]) -> Principal:
        principal = await self.verifier.verify_service_token(token, audience, scopes)
        principal.require(*scopes)
        return principal
