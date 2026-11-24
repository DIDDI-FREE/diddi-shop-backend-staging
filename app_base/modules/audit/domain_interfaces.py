from typing import Protocol


class AuditPort(Protocol):
    async def append(self, action: str, actor: str, resource: str, payload: dict) -> None: ...
