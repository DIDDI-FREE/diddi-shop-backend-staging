from app_base.core.observability import log_event


class ObservabilityService:
    async def record_external_call(self, service: str, operation: str, status: str, duration_ms: int) -> None:
        log_event("external.call", service=service, operation=operation, status=status, duration_ms=duration_ms)
