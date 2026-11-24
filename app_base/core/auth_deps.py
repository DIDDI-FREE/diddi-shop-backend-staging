from dataclasses import dataclass

from fastapi import Header


@dataclass(frozen=True)
class Actor:
    subject: str
    actor_type: str
    scopes: frozenset[str] = frozenset()


async def current_actor(x_actor_id: str | None = Header(default=None)) -> Actor:
    return Actor(subject=x_actor_id or "anonymous", actor_type="user")
