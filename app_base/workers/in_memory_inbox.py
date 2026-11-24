import hashlib
import json

from app_base.shared_kernel.contracts.events import ExternalEvent


class InMemoryProcessedEvents:
    def __init__(self):
        self.items: dict[tuple[str, str], str] = {}

    async def seen(self, consumer: str, event_id: str) -> bool:
        return (consumer, event_id) in self.items

    async def mark(self, consumer: str, event: ExternalEvent, result_hash: str) -> None:
        self.items[(consumer, event.event_id)] = result_hash

    @staticmethod
    def hash_payload(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
