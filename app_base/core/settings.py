from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIDDI_SHOP_", extra="ignore")

    app_name: str = "diddi-shop"
    environment: str = "development"
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
    service_client_id: str = "diddishop"
    service_tokens: dict[str, str] = {}
    service_keys: dict[str, str] = {}
    jwt_audience: str = "diddishop"
    diddifreeid_issuer: str = ""
    diddifreeid_jwks_url: str = ""
    diddipay_webhook_secret: str = ""
    diddisend_webhook_secret: str = ""
    order_seller_confirmation_hours: int = 24
    claim_window_hours: int = 72
    seller_release_delay_hours: int = 72
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
