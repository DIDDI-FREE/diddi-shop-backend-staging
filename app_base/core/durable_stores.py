import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_base.core.idempotency import IdempotencyRecord
from app_base.core.outbox import OutboxMessage
from app_base.core.platform_models import IdempotencyRecordModel, InboxEventModel, OutboxEventModel
from app_base.shared_kernel.contracts.events import ExternalEvent


class SqlOutboxStore:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def append(self, message: OutboxMessage) -> None:
        async with self.factory() as session, session.begin():
            session.add(OutboxEventModel(
                event_id=message.event_id,
                event_type=message.event_type,
                aggregate_type=message.aggregate_type,
                aggregate_id=message.aggregate_id,
                payload=json.dumps(message.payload, separators=(",", ":"), default=str),
                attempts=message.attempts,
                available_at=message.available_at,
                published_at=message.published_at,
                last_error=message.last_error,
            ))

    async def pending(self, limit: int = 100) -> list[OutboxMessage]:
        now = datetime.now(UTC)
        async with self.factory() as session:
            result = await session.execute(
                select(OutboxEventModel)
                .where(OutboxEventModel.published_at.is_(None), OutboxEventModel.available_at <= now)
                .order_by(OutboxEventModel.id)
                .limit(limit)
            )
            return [
                OutboxMessage(
                    event_id=row.event_id,
                    event_type=row.event_type,
                    aggregate_type=row.aggregate_type,
                    aggregate_id=row.aggregate_id,
                    payload=json.loads(row.payload),
                    available_at=row.available_at,
                    attempts=row.attempts,
                    published_at=row.published_at,
                    last_error=row.last_error,
                )
                for row in result.scalars()
            ]

    async def mark_published(self, event_id: str) -> None:
        async with self.factory() as session, session.begin():
            await session.execute(
                update(OutboxEventModel)
                .where(OutboxEventModel.event_id == event_id)
                .values(published_at=datetime.now(UTC))
            )

    async def mark_failed(self, event_id: str, error: str, attempts: int) -> None:
        delay = min(3600, 2 ** min(attempts, 10))
        async with self.factory() as session, session.begin():
            await session.execute(
                update(OutboxEventModel)
                .where(OutboxEventModel.event_id == event_id)
                .values(
                    attempts=attempts,
                    last_error=error[:4000],
                    available_at=datetime.now(UTC) + timedelta(seconds=delay),
                )
            )


class SqlInboxStore:
    def __init__(self, factory: async_sessionmaker[AsyncSession]):
        self.factory = factory

    async def seen(self, consumer: str, event_id: str) -> bool:
        async with self.factory() as session:
            result = await session.execute(
                select(InboxEventModel.id).where(
                    InboxEventModel.consumer == consumer,
                    InboxEventModel.event_id == event_id,
                )
            )
            return result.scalar_one_or_none() is not None

    async def mark(self, consumer: str, event: ExternalEvent, result_hash: str) -> None:
        async with self.factory() as session, session.begin():
            try:
                session.add(InboxEventModel(
                    consumer=consumer,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    result_hash=result_hash,
                ))
                await session.flush()
            except IntegrityError:
                await session.rollback()


class SqlIdempotencyStore:
    def __init__(self, factory: async_sessionmaker[AsyncSession], scope: str):
        self.factory = factory
        self.scope = scope

    async def get(self, key: str) -> IdempotencyRecord | None:
        async with self.factory() as session:
            result = await session.execute(
                select(IdempotencyRecordModel).where(
                    IdempotencyRecordModel.scope == self.scope,
                    IdempotencyRecordModel.key == key,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return IdempotencyRecord(
                key=row.key,
                request_hash=row.request_hash,
                status_code=row.status_code,
                response_body=json.loads(row.response_body),
            )

    async def save(self, record: IdempotencyRecord) -> None:
        async with self.factory() as session, session.begin():
            try:
                session.add(IdempotencyRecordModel(
                    scope=self.scope,
                    key=record.key,
                    request_hash=record.request_hash,
                    status_code=record.status_code,
                    response_body=json.dumps(record.response_body, separators=(",", ":")),
                ))
                await session.flush()
            except IntegrityError:
                await session.rollback()
