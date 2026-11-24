from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass
class OutboxMessage:
    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    available_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attempts: int = 0
    published_at: datetime | None = None
    last_error: str | None = None


async def append_outbox(target, message: OutboxMessage) -> None:
    """Append to either the test list or a durable outbox port."""
    append = target.append
    result = append(message)
    if hasattr(result, "__await__"):
        await result


def new_outbox_message(event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> OutboxMessage:
    return OutboxMessage(
        event_id=str(uuid4()),
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )
