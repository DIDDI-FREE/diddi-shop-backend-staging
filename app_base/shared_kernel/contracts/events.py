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


class DiddiPayCallbackEnvelope(BaseModel):
    """Callback envelope emitted by DiddiPay's payment outbox delivery."""

    id: str
    type: str
    occurred_at: datetime
    data: dict[str, Any]


class DiddiSendCallbackEnvelope(BaseModel):
    """Callback envelope emitted by DiddiSend's delivery outbox."""

    event_id: str
    event_version: str | int = 1
    event_type: str
    source_service: str
    delivery_id: str
    order_reference: str | None = None
    status: str | None = None
    origin_module: str | None = None
    currency: str = "XOF"
    financial_breakdown: dict[str, Any] | None = None
    occurred_at: datetime
    data: dict[str, Any]
