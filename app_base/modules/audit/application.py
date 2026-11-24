import json

from app_base.core.request_context import get_request_context


class AuditService:
    def __init__(self, factory=None):
        self.factory = factory
        self.events: list[dict] = []

    async def append(self, action: str, actor: str, resource: str, payload: dict) -> None:
        context = get_request_context()
        event = {
            "action": action,
            "actor": actor,
            "resource": resource,
            "payload": payload,
            "correlation_id": context.correlation_id if context else None,
        }
        self.events.append(event)
        if self.factory is not None:
            from app_base.core.platform_models import AuditEventModel

            async with self.factory() as session, session.begin():
                session.add(AuditEventModel(
                    action=action,
                    actor=actor,
                    resource=resource,
                    payload=json.dumps(payload, separators=(",", ":"), default=str),
                    correlation_id=event["correlation_id"],
                ))
