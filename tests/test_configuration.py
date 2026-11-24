import pytest

from app_base.core.settings import Settings


def _staging_settings(**overrides: str) -> Settings:
    values = {
        "environment": "staging",
        "diddifreeid_base_url": "https://auth-staging.diddifree.com",
        "diddipay_base_url": "https://pay-api-staging.diddifree.com/payfund/v1",
        "diddisend_base_url": "https://diddisend-api-staging.diddifree.com",
        "diddifiles_base_url": "https://diddifiles.diddifree.com",
        "diddirewards_base_url": "https://diddi-rewards-staging.diddifree.com",
        "diddicomms_base_url": "https://diddi-comm-staging.diddifree.com",
        "diddisupport_base_url": "https://support-backend-staging.diddifree.com",
        "diddiobserve_base_url": "https://logs-otel.diddifree.com",
        "service_client_ids": {
            "diddipay": "diddishop-staging-diddipay",
            "diddisend": "diddishop-staging-diddisend",
            "diddifiles": "diddishop-staging-diddifiles",
            "diddirewards": "diddishop-staging-diddirewards",
            "diddicomms": "diddishop-staging-diddicomms",
            "diddisupport": "diddishop-staging-diddisupport",
        },
        "service_client_secrets": {
            "diddipay": "pay-secret",
            "diddisend": "send-secret",
            "diddifiles": "files-secret",
            "diddirewards": "rewards-secret",
            "diddicomms": "comms-secret",
            "diddisupport": "support-secret",
        },
    }
    values.update(overrides)
    return Settings(**values)


def test_staging_configuration_requires_all_https_service_urls():
    _staging_settings().validate_external_configuration()


def test_staging_configuration_rejects_missing_service_url():
    settings = _staging_settings(diddisend_base_url="")
    with pytest.raises(ValueError, match="diddisend"):
        settings.validate_external_configuration()


def test_staging_configuration_rejects_http_service_url():
    settings = _staging_settings(diddipay_base_url="http://pay-api-staging.diddifree.com/payfund/v1")
    with pytest.raises(ValueError, match="diddipay"):
        settings.validate_external_configuration()
