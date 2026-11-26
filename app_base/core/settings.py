from functools import lru_cache
from uuid import UUID

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIDDI_SHOP_", extra="ignore")

    app_name: str = "diddi-shop"
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("DIDDI_SHOP_ENVIRONMENT", "ENVIRONMENT", "environment"),
    )
    database_url: str = "postgresql+asyncpg://diddishop:change-me@localhost:5432/diddishop"
    redis_url: str = "redis://localhost:6379/0"
    diddifreeid_base_url: str = ""
    diddipay_base_url: str = ""
    diddisend_base_url: str = ""
    diddifiles_base_url: str = ""
    diddifiles_s3_endpoint: str = ""
    diddirewards_base_url: str = ""
    diddicomms_base_url: str = ""
    diddisupport_base_url: str = ""
    diddiobserve_base_url: str = ""
    internal_request_timeout_seconds: float = 10.0
    # DiddiObserve uses a dedicated OTLP HTTP credential, not a DiddiFreeID
    # business credential. Keep these aliases compatible with both Compose
    # variables and direct Settings(...) construction in tests.
    otel_service_name: str = Field(
        default="diddishop",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME", "DIDDI_SHOP_OTEL_SERVICE_NAME", "otel_service_name"),
    )
    otel_environment: str = Field(
        default="",
        validation_alias=AliasChoices("OTEL_ENVIRONMENT", "DIDDI_SHOP_OTEL_ENVIRONMENT", "otel_environment"),
    )
    deployment_id: str = Field(
        default="",
        validation_alias=AliasChoices("DEPLOYMENT_ID", "DIDDI_SHOP_DEPLOYMENT_ID", "deployment_id"),
    )
    otel_service_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("OTEL_SERVICE_VERSION", "DIDDI_SHOP_OTEL_SERVICE_VERSION", "otel_service_version"),
    )
    otel_instance_id: str = Field(
        default="",
        validation_alias=AliasChoices("OTEL_INSTANCE_ID", "DIDDI_SHOP_OTEL_INSTANCE_ID", "otel_instance_id"),
    )
    diddi_component: str = Field(
        default="api",
        validation_alias=AliasChoices("DIDDI_COMPONENT", "DIDDI_SHOP_DIDDI_COMPONENT", "diddi_component"),
    )
    otel_exporter_otlp_protocol: str = Field(
        default="http/protobuf",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_PROTOCOL",
            "DIDDI_SHOP_OTEL_EXPORTER_OTLP_PROTOCOL",
            "otel_exporter_otlp_protocol",
        ),
    )
    otel_logs_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("OTEL_LOGS_ENABLED", "DIDDI_SHOP_OTEL_LOGS_ENABLED", "otel_logs_enabled"),
    )
    otel_exporter_otlp_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "DIDDI_SHOP_OTEL_EXPORTER_OTLP_ENDPOINT",
            "otel_exporter_otlp_endpoint",
        ),
    )
    otel_exporter_otlp_logs_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
            "DIDDI_SHOP_OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
            "otel_exporter_otlp_logs_endpoint",
        ),
    )
    otel_exporter_otlp_traces_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "DIDDI_SHOP_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "otel_exporter_otlp_traces_endpoint",
        ),
    )
    otel_exporter_otlp_headers: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_HEADERS",
            "DIDDI_SHOP_OTEL_EXPORTER_OTLP_HEADERS",
            "otel_exporter_otlp_headers",
        ),
    )
    # Legacy/static values are development-only compatibility inputs.
    service_client_id: str = "diddishop"
    service_tokens: dict[str, str] = Field(default_factory=dict)
    service_keys: dict[str, str] = Field(default_factory=dict)
    diddifreeid_service_token_url: str = ""
    service_client_ids: dict[str, str] = Field(default_factory=dict)
    service_client_secrets: dict[str, str] = Field(default_factory=dict)
    diddisend_client_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DIDDISEND_CLIENT_ID", "DIDDI_SHOP_DIDDISEND_CLIENT_ID", "diddisend_client_id"
        ),
    )
    diddisend_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DIDDISEND_CLIENT_SECRET", "DIDDI_SHOP_DIDDISEND_CLIENT_SECRET", "diddisend_client_secret"
        ),
    )
    diddisend_audience: str = Field(
        default="diddisend",
        validation_alias=AliasChoices(
            "DIDDISEND_AUDIENCE", "DIDDI_SHOP_DIDDISEND_AUDIENCE", "diddisend_audience"
        ),
    )
    diddisend_origin_service: str = Field(
        default="diddishop",
        validation_alias=AliasChoices(
            "DIDDISEND_ORIGIN_SERVICE", "DIDDI_SHOP_DIDDISEND_ORIGIN_SERVICE", "diddisend_origin_service"
        ),
    )
    diddisend_service_user_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DIDDISEND_SERVICE_USER_ID", "DIDDI_SHOP_DIDDISEND_SERVICE_USER_ID", "diddisend_service_user_id"
        ),
    )
    jwt_audience: str = "diddishop"
    diddifreeid_issuer: str = ""
    diddifreeid_jwks_url: str = ""
    diddipay_webhook_secret: str = ""
    diddisend_webhook_secret: str = ""
    order_seller_confirmation_hours: int = 24
    claim_window_hours: int = 72
    seller_release_delay_hours: int = 72
    seller_release_enabled: bool = False
    seller_commission_bps: int = 1000

    def validate_external_configuration(self) -> None:
        """Fail closed for non-development deployments without exposing secrets."""
        if self.environment == "development":
            return
        required = {
            "diddifreeid": self.diddifreeid_base_url,
            "diddipay": self.diddipay_base_url,
            "diddisend": self.diddisend_base_url,
            "diddifiles": self.diddifiles_base_url,
            "diddirewards": self.diddirewards_base_url,
            "diddicomms": self.diddicomms_base_url,
            "diddisupport": self.diddisupport_base_url,
            "diddiobserve": self.diddiobserve_base_url,
        }
        missing = sorted(name for name, url in required.items() if not url.strip())
        if missing:
            raise ValueError(f"Missing external service URLs: {', '.join(missing)}")
        insecure = sorted(
            name for name, url in required.items() if not url.lower().startswith("https://")
        )
        if insecure:
            raise ValueError(f"HTTPS is required for external services: {', '.join(insecure)}")
        token_targets = (
            "diddipay",
            "diddisend",
            "diddifiles",
            "diddirewards",
            "diddicomms",
            "diddisupport",
        )
        client_ids = dict(self.service_client_ids)
        client_secrets = dict(self.service_client_secrets)
        if self.diddisend_client_id.strip():
            client_ids["diddisend"] = self.diddisend_client_id
        if self.diddisend_client_secret.strip():
            client_secrets["diddisend"] = self.diddisend_client_secret
        missing_client_ids = sorted(name for name in token_targets if not client_ids.get(name, "").strip())
        if missing_client_ids:
            raise ValueError(f"Missing S2S client IDs: {', '.join(missing_client_ids)}")
        missing_client_secrets = sorted(name for name in token_targets if not client_secrets.get(name, "").strip())
        if missing_client_secrets:
            raise ValueError(f"Missing S2S client secrets: {', '.join(missing_client_secrets)}")
        if not self.diddisend_service_user_id.strip():
            raise ValueError("Missing DiddiSend technical sender UUID: DIDDISEND_SERVICE_USER_ID")
        try:
            UUID(self.diddisend_service_user_id)
        except ValueError as exc:
            raise ValueError("DIDDISEND_SERVICE_USER_ID must be a valid UUID") from exc
        if self.otel_logs_enabled:
            if self.otel_exporter_otlp_protocol != "http/protobuf":
                raise ValueError("DiddiObserve requires OTLP HTTP/protobuf")
            telemetry_endpoints = {
                "otel_exporter_otlp_logs_endpoint": self.otel_exporter_otlp_logs_endpoint,
                "otel_exporter_otlp_traces_endpoint": self.otel_exporter_otlp_traces_endpoint,
            }
            missing_telemetry = sorted(name for name, value in telemetry_endpoints.items() if not value.strip())
            if missing_telemetry:
                raise ValueError(f"Missing DiddiObserve OTLP endpoints: {', '.join(missing_telemetry)}")
            insecure_telemetry = sorted(
                name for name, value in telemetry_endpoints.items() if not value.lower().startswith("https://")
            )
            if insecure_telemetry:
                raise ValueError(f"HTTPS is required for DiddiObserve OTLP endpoints: {', '.join(insecure_telemetry)}")
            if not self.otel_exporter_otlp_headers.strip():
                raise ValueError("Missing DiddiObserve OTLP headers")


@lru_cache
def get_settings() -> Settings:
    return Settings()
