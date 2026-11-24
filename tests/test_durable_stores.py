import json

import pytest

from app_base.core.outbox import new_outbox_message
from app_base.workers.outbox_worker import publish_pending


@pytest.mark.asyncio
async def test_outbox_worker_does_not_republish_published_messages():
    message = new_outbox_message("order.created", "order", "order-1", {"ok": True})
    messages = [message]
    published = []

    class Publisher:
        async def publish(self, item):
            published.append(json.dumps(item.payload, sort_keys=True))

    assert await publish_pending(messages, Publisher()) == 1
    assert await publish_pending(messages, Publisher()) == 0
    assert published == ['{"ok": true}']
