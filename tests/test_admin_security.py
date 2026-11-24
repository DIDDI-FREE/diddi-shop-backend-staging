import pytest

from app_base.core.auth_deps import Actor
from app_base.core.errors import ConflictError
from app_base.core.idempotency import (
    IdempotencyRecord,
    InMemoryIdempotencyStore,
    replay_or_none,
    request_hash,
)


def test_admin_roles_are_distinct_from_regular_users():
    assert Actor("user-1", "user").actor_type != "admin"
    assert Actor("admin-1", "admin").actor_type == "admin"


@pytest.mark.asyncio
async def test_idempotency_store_replays_same_admin_command():
    store = InMemoryIdempotencyStore()
    body = {"decision": "buyer", "reason": "damaged", "amount_to_refund": 100}
    await store.save(IdempotencyRecord("key-1", request_hash(body), 200, {"ok": True}))
    replay = await replay_or_none(store, "key-1", body)
    assert replay.response_body == {"ok": True}
    with pytest.raises(ConflictError):
        await replay_or_none(store, "key-1", {"decision": "seller"})
