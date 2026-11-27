import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx
import jwt
from fastapi import Header, HTTPException, Request
from jwt import PyJWK

_VERIFY_DEFAULT = object()
logger = logging.getLogger("diddi_shop.auth")


@dataclass(frozen=True)
class Actor:
    subject: str
    actor_type: str
    scopes: frozenset[str] = frozenset()


def actor_from_claims(claims: dict[str, Any]) -> Actor:
    subject = str(claims.get("sub") or claims.get("user_id") or "")
    if not subject:
        raise HTTPException(status_code=401, detail="JWT subject is required")
    actor_type = "service" if str(subject).startswith("service:") else str(
        claims.get("actor_type", "user")
    )
    roles = set(claims.get("roles", [])) if isinstance(claims.get("roles", []), list) else set()
    if roles & {"admin", "support", "backoffice"}:
        actor_type = "admin" if "admin" in roles or "backoffice" in roles else "support"
    raw_scopes = claims.get("scope", claims.get("scp", ""))
    scopes = frozenset(raw_scopes if isinstance(raw_scopes, list) else str(raw_scopes).split())
    return Actor(subject=subject, actor_type=actor_type, scopes=scopes)


class JwtVerifier:
    def __init__(self, *, jwks_url: str, audience: str | None, issuer: str = "", ttl_seconds: int = 300):
        self.jwks_url = jwks_url
        self.audience = audience or None
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
                keys[item["kid"]] = PyJWK.from_dict(item).key
        if not keys:
            raise ValueError("DiddiFreeID JWKS did not contain usable keys")
        self._keys = keys
        self._loaded_at = monotonic()
        return keys

    async def verify(self, token: str, *, audience: str | None | object = _VERIFY_DEFAULT) -> Actor:
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
            expected_audience = self.audience if audience is _VERIFY_DEFAULT else audience
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=expected_audience,
                issuer=self.issuer,
                options=options,
            )
            return actor_from_claims(claims)
        except (ValueError, jwt.PyJWTError, httpx.HTTPError) as exc:
            # Keep the client response generic, but retain the precise safe
            # rejection reason for staging/production troubleshooting.
            logger.warning("DiddiFreeID JWT rejected (%s): %s", type(exc).__name__, exc)
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
    # DiddiFreeID user access tokens currently carry iss/sub/exp but no aud.
    # Audience validation remains explicit for service-to-service routes below.
    return await verifier.verify(authorization.removeprefix("Bearer ").strip(), audience=None)


async def current_service_actor(
    request: Request,
    authorization: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
) -> Actor:
    """Authenticate an internal route as a service-to-service caller.

    Development keeps the local actor shortcut for tests. Non-development
    deployments accept only a DiddiFreeID service principal, never a browser
    user or an operator JWT.
    """
    if request.app.state.settings.environment == "development":
        actor = Actor(subject=x_actor_id or "anonymous", actor_type="user")
    else:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        verifier: JwtVerifier = request.app.state.jwt_verifier
        actor = await verifier.verify(
            authorization.removeprefix("Bearer ").strip(),
            audience=request.app.state.settings.jwt_audience or "diddishop",
        )
    if request.app.state.settings.environment != "development" and actor.actor_type != "service":
        raise HTTPException(status_code=403, detail="service principal required")
    return actor
