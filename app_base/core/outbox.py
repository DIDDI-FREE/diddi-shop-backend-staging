from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class OutboxMessage:
    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    available_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    published_at: datetime | None = None
    last_error: str | None = None


def new_outbox_message(event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> OutboxMessage:
    return OutboxMessage(
        event_id=str(uuid4()),
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )
