from __future__ import annotations

import logging
import random
import threading
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from opentelemetry import _logs as logs
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import encode_logs
from opentelemetry.exporter.otlp.proto.http.trace_exporter import encode_spans
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    LogExportResult,
    LogRecordExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

from app_base.core.settings import Settings

MAX_EVENT_BYTES = 64 * 1024
MAX_REQUEST_BYTES = 4 * 1024 * 1024
EXPORT_TIMEOUT_SECONDS = 5.0
RETRYABLE_STATUSES = {429, 502, 503, 504}
MAX_ATTEMPTS = 4


class TelemetryStats:
    """Small process-local counters for loss/rejection visibility."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, int] = {
            "exported_records": 0,
            "retry_count": 0,
            "dropped_records": 0,
            "rejected_records": 0,
        }

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._values[name] = self._values.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._values)


def parse_otlp_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in raw.split(","):
        key, separator, value = item.partition("=")
        if separator and key.strip() and value.strip():
            headers[key.strip()] = value.strip()
    return headers


def retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        try:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                target = target.replace(tzinfo=UTC)
            return max((target - datetime.now(UTC)).total_seconds(), 0.0)
        except (TypeError, ValueError, OverflowError):
            return None


class _OtlpHttpExporter:
    def __init__(self, endpoint: str, headers: dict[str, str], stats: TelemetryStats) -> None:
        self.endpoint = endpoint
        self.headers = {**headers, "Content-Type": "application/x-protobuf"}
        self.stats = stats
        self._shutdown = False

    def _post(self, payload: bytes, count: int) -> bool:
        for attempt in range(MAX_ATTEMPTS):
            request = Request(self.endpoint, data=payload, headers=self.headers, method="POST")
            try:
                with urlopen(request, timeout=EXPORT_TIMEOUT_SECONDS) as response:
                    if 200 <= response.status < 300:
                        self.stats.increment("exported_records", count)
                        return True
                    status = response.status
                    retry_after = response.headers.get("Retry-After")
            except HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
            except (TimeoutError, URLError, OSError):
                status = None
                retry_after = None

            if status in RETRYABLE_STATUSES or status is None:
                if attempt < MAX_ATTEMPTS - 1:
                    self.stats.increment("retry_count")
                    delay = retry_after_seconds(retry_after)
                    if delay is None:
                        delay = min(2.0, 0.25 * (2**attempt))
                    time.sleep(min(delay, 5.0) * random.uniform(0.8, 1.2))
                    continue
                self.stats.increment("dropped_records", count)
                return False

            # 400/401/403/404/413 and all other non-retryable responses are
            # producer rejections, not transient delivery failures.
            self.stats.increment("rejected_records", count)
            return False
        return False

    def _export_proto(self, payload: Any, count: int) -> bool:
        serialized = payload.SerializeToString()
        if len(serialized) <= MAX_REQUEST_BYTES:
            return self._post(serialized, count)
        if count <= 1:
            self.stats.increment("dropped_records", count)
            return False
        return False

    def shutdown(self) -> None:
        self._shutdown = True


class OtlpSpanExporter(_OtlpHttpExporter, SpanExporter):
    def export(self, spans: Sequence[Any]) -> SpanExportResult:
        if self._shutdown:
            return SpanExportResult.FAILURE
        if not spans:
            return SpanExportResult.SUCCESS
        if len(encode_spans(spans).SerializeToString()) > MAX_REQUEST_BYTES and len(spans) > 1:
            midpoint = len(spans) // 2
            left = self.export(spans[:midpoint])
            right = self.export(spans[midpoint:])
            return SpanExportResult.SUCCESS if left == right == SpanExportResult.SUCCESS else SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS if self._export_proto(encode_spans(spans), len(spans)) else SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 10_000) -> bool:
        return not self._shutdown


class OtlpLogExporter(_OtlpHttpExporter, LogRecordExporter):
    def export(self, batch: Sequence[Any]) -> LogExportResult:
        if self._shutdown:
            return LogExportResult.FAILURE
        if not batch:
            return LogExportResult.SUCCESS
        payload = encode_logs(batch)
        if len(payload.SerializeToString()) > MAX_REQUEST_BYTES and len(batch) > 1:
            midpoint = len(batch) // 2
            left = self.export(batch[:midpoint])
            right = self.export(batch[midpoint:])
            return LogExportResult.SUCCESS if left == right == LogExportResult.SUCCESS else LogExportResult.FAILURE
        return LogExportResult.SUCCESS if self._export_proto(payload, len(batch)) else LogExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 10_000) -> bool:
        return not self._shutdown


class DiddiTelemetryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = message[:MAX_EVENT_BYTES]
        record.args = ()
        return True


_resource_attributes: dict[str, str] = {
    "service.name": "diddishop",
    "service.namespace": "diddi",
}


def resource_attributes() -> dict[str, str]:
    return dict(_resource_attributes)


class TelemetryRuntime:
    def __init__(
        self,
        stats: TelemetryStats,
        tracer_provider: TracerProvider | None = None,
        logger_provider: LoggerProvider | None = None,
        handler: LoggingHandler | None = None,
    ) -> None:
        self.stats = stats
        self.tracer_provider = tracer_provider
        self.logger_provider = logger_provider
        self.handler = handler

    def shutdown(self) -> None:
        logger = logging.getLogger("diddi_shop")
        if self.handler is not None:
            logger.removeHandler(self.handler)
        if self.logger_provider is not None:
            self.logger_provider.force_flush(5000)
            self.logger_provider.shutdown()
        if self.tracer_provider is not None:
            self.tracer_provider.force_flush(5000)
            self.tracer_provider.shutdown()


def configure_telemetry(settings: Settings) -> TelemetryRuntime:
    stats = TelemetryStats()
    environment = settings.otel_environment or settings.environment
    attributes = {
        "service.name": settings.otel_service_name,
        "service.namespace": "diddi",
        "service.version": settings.otel_service_version,
        "service.instance.id": settings.otel_instance_id or "unknown",
        "deployment.environment": environment,
        "deployment.id": settings.deployment_id or "unknown",
        "diddi.component": settings.diddi_component,
    }
    _resource_attributes.clear()
    _resource_attributes.update(attributes)
    resource = Resource.create(attributes)
    headers = parse_otlp_headers(settings.otel_exporter_otlp_headers)
    tracer_provider: TracerProvider | None = None
    logger_provider: LoggerProvider | None = None
    handler: LoggingHandler | None = None

    if settings.otel_exporter_otlp_traces_endpoint:
        tracer_provider = TracerProvider(resource=resource, shutdown_on_exit=False)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OtlpSpanExporter(settings.otel_exporter_otlp_traces_endpoint, headers, stats),
                max_queue_size=2048,
                schedule_delay_millis=5000,
                max_export_batch_size=512,
                export_timeout_millis=5000,
            )
        )
        trace.set_tracer_provider(tracer_provider)

    if settings.otel_logs_enabled and settings.otel_exporter_otlp_logs_endpoint:
        logger_provider = LoggerProvider(resource=resource, shutdown_on_exit=False)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OtlpLogExporter(settings.otel_exporter_otlp_logs_endpoint, headers, stats),
                max_queue_size=2048,
                schedule_delay_millis=5000,
                max_export_batch_size=512,
                export_timeout_millis=5000,
            )
        )
        logs.set_logger_provider(logger_provider)
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        handler.set_name("diddiobserve-otlp")
        handler.addFilter(DiddiTelemetryFilter())
        application_logger = logging.getLogger("diddi_shop")
        application_logger.setLevel(logging.INFO)
        application_logger.propagate = False
        for existing in tuple(application_logger.handlers):
            if existing.get_name() == "diddiobserve-otlp":
                application_logger.removeHandler(existing)
        application_logger.addHandler(handler)

    return TelemetryRuntime(stats, tracer_provider, logger_provider, handler)
