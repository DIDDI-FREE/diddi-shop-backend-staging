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
