from collections.abc import Awaitable, Callable

from app_base.shared_kernel.contracts.events import ExternalEvent


class ProcessedEventsPort:
    async def seen(self, consumer: str, event_id: str) -> bool:
        raise NotImplementedError

    async def mark(self, consumer: str, event: ExternalEvent, result_hash: str) -> None:
        raise NotImplementedError


async def process_once(
    *,
    consumer: str,
    event: ExternalEvent,
    inbox: ProcessedEventsPort,
    handler: Callable[[ExternalEvent], Awaitable[None]],
    result_hash: str,
) -> bool:
    if await inbox.seen(consumer, event.event_id):
        return False
    await handler(event)
    await inbox.mark(consumer, event, result_hash)
    return True
