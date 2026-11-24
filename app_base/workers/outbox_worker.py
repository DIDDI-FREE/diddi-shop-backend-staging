from app_base.core.outbox import OutboxMessage


async def publish_pending(messages: list[OutboxMessage], publisher) -> int:
    published = 0
    for message in messages:
        if message.published_at is not None:
            continue
        try:
            await publisher.publish(message)
            message.published_at = message.available_at
            published += 1
        except Exception as exc:
            message.attempts += 1
            message.last_error = str(exc)
    return published


async def publish_durable_pending(store, publisher, limit: int = 100) -> int:
    published = 0
    for message in await store.pending(limit):
        try:
            await publisher.publish(message)
            await store.mark_published(message.event_id)
            published += 1
        except Exception as exc:
            await store.mark_failed(message.event_id, str(exc), message.attempts + 1)
    return published
