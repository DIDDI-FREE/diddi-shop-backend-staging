import json

from redis.asyncio import Redis

from app_base.core.outbox import OutboxMessage


class RedisAdapter:
    def __init__(self, client: Redis):
        self.client = client

    async def publish(self, stream: str, fields: dict[str, str]) -> str:
        return await self.client.xadd(stream, fields)

    async def acquire_lock(self, key: str, token: str, ttl_seconds: int) -> bool:
        return bool(await self.client.set(key, token, nx=True, ex=ttl_seconds))

    async def release_lock(self, key: str, token: str) -> bool:
        current = await self.client.get(key)
        if current is None or (current.decode() if isinstance(current, bytes) else current) != token:
            return False
        return bool(await self.client.delete(key))


class RedisOutboxPublisher:
    def __init__(self, client: Redis, stream: str = "diddishop.events.v1"):
        self.client = client
        self.stream = stream

    async def publish(self, message: OutboxMessage) -> str:
        return await self.client.xadd(self.stream, {
            "event_id": message.event_id,
            "event_type": message.event_type,
            "aggregate_id": message.aggregate_id,
            "payload": json.dumps(message.payload, separators=(",", ":"), default=str),
        })
