from dataclasses import dataclass
from hashlib import sha256
import json

from app_base.core.errors import ConflictError


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    request_hash: str
    status_code: int
    response_body: dict


class IdempotencyPort:
    async def get(self, key: str) -> IdempotencyRecord | None:
        raise NotImplementedError

    async def save(self, record: IdempotencyRecord) -> None:
        raise NotImplementedError


def request_hash(body: dict) -> str:
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


async def replay_or_none(store: IdempotencyPort, key: str, body: dict) -> IdempotencyRecord | None:
    record = await store.get(key)
    if record is not None and record.request_hash != request_hash(body):
        raise ConflictError("Idempotency-Key reused with a different request body")
    return record
