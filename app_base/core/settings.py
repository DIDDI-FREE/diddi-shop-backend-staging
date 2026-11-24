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
    diddimap_base_url: str = ""
    diddifiles_base_url: str = ""
    diddirewards_base_url: str = ""
    diddicomms_base_url: str = ""
    diddisupport_base_url: str = ""
    diddiobserve_base_url: str = ""
    internal_request_timeout_seconds: float = 10.0
    service_client_id: str = "diddishop"
    service_tokens: dict[str, str] = {}
    service_keys: dict[str, str] = {}
    jwt_audience: str = "diddishop"
    order_seller_confirmation_hours: int = 24
    claim_window_hours: int = 72
    seller_release_delay_hours: int = 72
    seller_commission_bps: int = 1000


@lru_cache
def get_settings() -> Settings:
    return Settings()
