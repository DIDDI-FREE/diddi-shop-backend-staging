import jwt
import pytest
from fastapi import HTTPException
from jwt import PyJWK

from app_base.core.auth_deps import JwtVerifier, actor_from_claims


def test_runtime_uses_pyjwt_with_jwk_support():
    assert jwt.__version__.split(".")[0] == "2"
    assert PyJWK is not None


def test_actor_from_user_claims_extracts_scopes():
    actor = actor_from_claims({"sub": "user-1", "scope": "shop:read shop:write"})
    assert actor.subject == "user-1"
    assert actor.actor_type == "user"
    assert actor.scopes == frozenset({"shop:read", "shop:write"})


def test_actor_from_service_claims_detects_service_actor():
    actor = actor_from_claims({"sub": "service:diddishop", "scp": ["diddisend:deliveries:create"]})
    assert actor.actor_type == "service"
    assert "diddisend:deliveries:create" in actor.scopes


def test_actor_claims_require_subject():
    with pytest.raises(HTTPException):
        actor_from_claims({"scope": "shop:read"})


@pytest.mark.asyncio
async def test_user_token_verification_can_skip_audience_when_diddifreeid_omits_it(monkeypatch):
    verifier = JwtVerifier(jwks_url="https://auth.example/jwks", audience="diddishop", issuer="diddifree-id")

    monkeypatch.setattr(jwt, "get_unverified_header", lambda _token: {"kid": "kid-1"})
    async def load_keys():
        return {"kid-1": object()}

    monkeypatch.setattr(verifier, "_load_keys", load_keys)
    captured: dict[str, object] = {}

    def decode(_token, **kwargs):
        captured.update(kwargs)
        return {"sub": "user-1", "exp": 1}

    monkeypatch.setattr(jwt, "decode", decode)

    actor = await verifier.verify("token", audience=None)

    assert actor.subject == "user-1"
    assert captured["audience"] is None
    assert captured["issuer"] == "diddifree-id"


@pytest.mark.asyncio
async def test_service_token_verification_keeps_explicit_audience(monkeypatch):
    verifier = JwtVerifier(jwks_url="https://auth.example/jwks", audience=None, issuer="diddifree-id")

    monkeypatch.setattr(jwt, "get_unverified_header", lambda _token: {"kid": "kid-1"})
    async def load_keys():
        return {"kid-1": object()}

    monkeypatch.setattr(verifier, "_load_keys", load_keys)
    captured: dict[str, object] = {}

    def decode(_token, **kwargs):
        captured.update(kwargs)
        return {"sub": "service:diddishop", "exp": 1}

    monkeypatch.setattr(jwt, "decode", decode)

    actor = await verifier.verify("token", audience="diddishop")

    assert actor.actor_type == "service"
    assert captured["audience"] == "diddishop"
