import json
import logging

import pytest
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, use_span

from app_base.core.observability import log_event
from app_base.core.settings import Settings
from app_base.core.telemetry import parse_otlp_headers, retry_after_seconds


def test_log_event_contains_contract_fields_and_redacts_sensitive_data(caplog):
    caplog.set_level(logging.INFO, logger="diddi_shop")
    span = NonRecordingSpan(
        SpanContext(
            trace_id=0x123,
            span_id=0x456,
            is_remote=False,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )
    )
    with use_span(span):
        log_event(
            "synthetic.test",
            message="synthetic marker",
            password="do-not-export",
            email="person@example.com",
            order_reference="order-1",
        )

    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["event"] == "synthetic.test"
    assert payload["message"] == "synthetic marker"
    assert payload["password"] == "[REDACTED]"
    assert payload["email"] == "[REDACTED]"
    assert payload["trace_id"] == "00000000000000000000000000000123"
    assert payload["span_id"] == "0000000000000456"
    assert payload["resource"]["service.name"] == "diddishop"


def test_otlp_headers_preserve_basic_padding_without_logging_secret():
    assert parse_otlp_headers("Authorization=Basic abc==,X-Test=value") == {
        "Authorization": "Basic abc==",
        "X-Test": "value",
    }


def test_retry_after_supports_seconds_and_invalid_values():
    assert retry_after_seconds("2") == 2.0
    assert retry_after_seconds("invalid") is None


def test_staging_telemetry_requires_complete_otlp_contract():
    settings = Settings(
        environment="staging",
        diddifreeid_base_url="https://auth.example",
        diddipay_base_url="https://pay.example",
        diddisend_base_url="https://send.example",
        diddifiles_base_url="https://files.example",
        diddirewards_base_url="https://rewards.example",
        diddicomms_base_url="https://comms.example",
        diddisupport_base_url="https://support.example",
        diddiobserve_base_url="https://observe.example",
        service_client_ids={service: f"shop-{service}" for service in (
            "diddipay", "diddisend", "diddifiles", "diddirewards", "diddicomms", "diddisupport"
        )},
        service_client_secrets={service: f"secret-{service}" for service in (
            "diddipay", "diddisend", "diddifiles", "diddirewards", "diddicomms", "diddisupport"
        )},
        otel_logs_enabled=True,
        otel_exporter_otlp_protocol="http/protobuf",
        otel_exporter_otlp_logs_endpoint="https://logs-otel.diddifree.com/otlp/diddishop/v1/logs",
        otel_exporter_otlp_traces_endpoint="",
        otel_exporter_otlp_headers="Authorization=Basic dedicated",
    )
    with pytest.raises(ValueError, match="Missing DiddiObserve OTLP endpoints"):
        settings.validate_external_configuration()
