from dataclasses import dataclass


@dataclass
class CommunicationService:
    adapter: object

    async def enqueue(self, event: dict) -> dict:
        event_id = event["event_id"]
        return await self.adapter.create_task(
            {
                "source_service": "diddishop",
                "event_id": event_id,
                "event_type": event["event_type"],
                "recipient_id": event["payload"].get("customer_id"),
                "payload": event["payload"],
            },
            f"shop:notify:{event_id}:1",
        )
