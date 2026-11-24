from typing import Protocol


class ObservabilityPort(Protocol):
    async def record(self, event: dict) -> None: ...
