from app_base.integrations.base import ServiceAdapter


class DiddiObserveAdapter(ServiceAdapter):
    async def export(self, payload: bytes, path: str = "/otlp/diddishop/v1/logs") -> None:
        """Legacy low-level adapter for protobuf payloads.

        The application uses the OpenTelemetry SDK for batching and retries;
        this adapter intentionally has no DiddiFreeID credential.
        """
        response = await self.request(
            "POST",
            path,
            content=payload,
            headers={"Content-Type": "application/x-protobuf"},
        )
        response.raise_for_status()
