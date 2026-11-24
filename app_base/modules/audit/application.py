from app_base.core.request_context import get_request_context


class AuditService:
    def __init__(self):
        self.events: list[dict] = []

    async def append(self, action: str, actor: str, resource: str, payload: dict) -> None:
        context = get_request_context()
        self.events.append({
            "action": action,
            "actor": actor,
            "resource": resource,
            "payload": payload,
            "correlation_id": context.correlation_id if context else None,
        })
