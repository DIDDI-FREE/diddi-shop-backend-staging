import pytest

from app_base.core.integration_registry import build_integrations
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
        "diddisend_service_user_id": "5cf96b1d-005a-49b8-b6b9-1a6c3c42fd7c",
        "diddisend_sender_phone": "+237690000000",
        "diddisend_sender_email": "shop@diddifree.com",
    }
    values.update(overrides)
    return Settings(**values)


def test_staging_configuration_requires_all_https_service_urls():
    _staging_settings().validate_external_configuration()


def test_payment_return_defaults_to_real_shop_route(monkeypatch):
    monkeypatch.delenv("DIDDI_SHOP_DIDDIPAY_RETURN_URL", raising=False)
    monkeypatch.delenv("DIDDI_SHOP_DIDDIPAY_RETURN_TARGET", raising=False)
    settings = Settings()
    assert settings.diddipay_return_url == "https://diddishop-backend.diddifree.com/payments/return"
    assert settings.diddipay_return_target == ""


def test_payment_return_can_be_overridden_from_environment(monkeypatch):
    monkeypatch.setenv("DIDDI_SHOP_DIDDIPAY_RETURN_URL", "https://app.diddifree.com/return")
    monkeypatch.setenv("DIDDI_SHOP_DIDDIPAY_RETURN_TARGET", "app")
    settings = Settings()
    assert settings.diddipay_return_url == "https://app.diddifree.com/return"
    assert settings.diddipay_return_target == "app"


def test_staging_configuration_rejects_missing_service_url():
    settings = _staging_settings(diddisend_base_url="")
    with pytest.raises(ValueError, match="diddisend"):
        settings.validate_external_configuration()


def test_staging_configuration_rejects_http_service_url():
    settings = _staging_settings(diddipay_base_url="http://pay-api-staging.diddifree.com/payfund/v1")
    with pytest.raises(ValueError, match="diddipay"):
        settings.validate_external_configuration()


def test_explicit_diddisend_credentials_override_generic_target_map():
    settings = _staging_settings(
        diddisend_client_id="diddishop-staging-diddisend",
        diddisend_client_secret="explicit-send-secret",
        diddisend_audience="diddisend",
        diddisend_origin_service="diddishop",
    )

    integration = build_integrations(settings).diddisend

    assert integration.credential is not None
    assert integration.credential.client_id == "diddishop-staging-diddisend"
    assert integration.credential.token_provider is not None
    assert integration.credential.token_provider.client_secret == "explicit-send-secret"
    assert integration.credential.token_provider.audience == "diddisend"
    assert integration.credential.origin_service == "diddishop"
    assert integration.credential.user_id == "5cf96b1d-005a-49b8-b6b9-1a6c3c42fd7c"
