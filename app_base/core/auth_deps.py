from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx
import jwt
from fastapi import Header, HTTPException, Request


@dataclass(frozen=True)
class Actor:
    subject: str
    actor_type: str
    scopes: frozenset[str] = frozenset()


def actor_from_claims(claims: dict[str, Any]) -> Actor:
    subject = str(claims.get("sub") or claims.get("user_id") or "")
    if not subject:
        raise HTTPException(status_code=401, detail="JWT subject is required")
    actor_type = "service" if str(subject).startswith("service:") else str(claims.get("actor_type", "user"))
    roles = set(claims.get("roles", [])) if isinstance(claims.get("roles", []), list) else set()
    if roles & {"admin", "support", "backoffice"}:
        actor_type = "admin" if "admin" in roles or "backoffice" in roles else "support"
    raw_scopes = claims.get("scope", claims.get("scp", ""))
    scopes = frozenset(raw_scopes if isinstance(raw_scopes, list) else str(raw_scopes).split())
    return Actor(subject=subject, actor_type=actor_type, scopes=scopes)


class JwtVerifier:
    def __init__(self, *, jwks_url: str, audience: str, issuer: str = "", ttl_seconds: int = 300):
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer or None
        self.ttl_seconds = ttl_seconds
        self._keys: dict[str, Any] = {}
        self._loaded_at = 0.0

    async def _load_keys(self) -> dict[str, Any]:
        if self._keys and monotonic() - self._loaded_at < self.ttl_seconds:
            return self._keys
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
        keys = {}
        for item in response.json().get("keys", []):
            if item.get("kid"):
                keys[item["kid"]] = jwt.algorithms.RSAAlgorithm.from_jwk(item)
        if not keys:
            raise ValueError("DiddiFreeID JWKS did not contain usable keys")
        self._keys = keys
        self._loaded_at = monotonic()
        return keys

    async def verify(self, token: str) -> Actor:
        try:
            header = jwt.get_unverified_header(token)
            keys = await self._load_keys()
            key = keys.get(header.get("kid"))
            if key is None:
                self._loaded_at = 0
                key = (await self._load_keys()).get(header.get("kid"))
            if key is None:
                raise ValueError("unknown JWT key id")
            options = {"require": ["exp", "sub"]}
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options=options,
            )
            return actor_from_claims(claims)
        except (ValueError, jwt.PyJWTError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=401, detail="Invalid DiddiFreeID token") from exc


async def current_actor(
    request: Request,
    authorization: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
) -> Actor:
    settings = request.app.state.settings
    if settings.environment == "development":
        return Actor(subject=x_actor_id or "anonymous", actor_type="user")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    verifier: JwtVerifier = request.app.state.jwt_verifier
    return await verifier.verify(authorization.removeprefix("Bearer ").strip())
