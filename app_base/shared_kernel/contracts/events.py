from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    event_version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    producer: str = "diddi-shop"
    aggregate_type: str
    aggregate_id: str
    correlation_id: str
    causation_id: str | None = None
    payload: dict[str, Any]


class ExternalEvent(BaseModel):
    """Normalized input after signature/auth validation by an adapter."""
    event_id: str
    event_type: str
    event_version: int = 1
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None
