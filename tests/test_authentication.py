import jwt
import pytest
from fastapi import HTTPException
from jwt import PyJWK

from app_base.core.auth_deps import actor_from_claims


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
