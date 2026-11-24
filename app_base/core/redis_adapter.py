from redis.asyncio import Redis


class RedisAdapter:
    def __init__(self, client: Redis):
        self.client = client

    async def publish(self, stream: str, fields: dict[str, str]) -> str:
        return await self.client.xadd(stream, fields)

    async def acquire_lock(self, key: str, token: str, ttl_seconds: int) -> bool:
        return bool(await self.client.set(key, token, nx=True, ex=ttl_seconds))

    async def release_lock(self, key: str, token: str) -> bool:
        current = await self.client.get(key)
        if current is None or current.decode() != token:
            return False
        return bool(await self.client.delete(key))
