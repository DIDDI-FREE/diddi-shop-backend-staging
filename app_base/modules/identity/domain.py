from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Principal:
    subject: str
    actor_type: str
    scopes: frozenset[str]
    claims: dict[str, object]

    def require(self, *scopes: str) -> None:
        missing = set(scopes) - self.scopes
        if missing:
            raise PermissionError(f"missing scopes: {', '.join(sorted(missing))}")


class TokenVerifier(Protocol):
    async def verify_user_token(self, token: str) -> Principal: ...
    async def verify_service_token(self, token: str, audience: str, scopes: set[str]) -> Principal: ...
