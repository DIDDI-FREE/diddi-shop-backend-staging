from dataclasses import dataclass

from app_base.core.service_scopes import required_scopes
from app_base.core.settings import Settings
from app_base.integrations.auth import ServiceCredential
from app_base.integrations.diddicomms import DiddiCommsAdapter
from app_base.integrations.diddifiles import DiddiFilesAdapter
from app_base.integrations.diddifreeid import DiddiFreeIDAdapter
from app_base.integrations.diddiobserve import DiddiObserveAdapter
from app_base.integrations.diddipay import DiddiPayAdapter
from app_base.integrations.diddirewards import DiddiRewardsAdapter
from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.integrations.diddisupport import DiddiSupportAdapter


@dataclass(frozen=True)
class IntegrationRegistry:
    """All external adapters are composed once and injected from app.state."""

    diddifreeid: DiddiFreeIDAdapter
    diddipay: DiddiPayAdapter
    diddisend: DiddiSendAdapter
    diddifiles: DiddiFilesAdapter
    diddirewards: DiddiRewardsAdapter
    diddicomms: DiddiCommsAdapter
    diddisupport: DiddiSupportAdapter
    diddiobserve: DiddiObserveAdapter


def build_integrations(settings: Settings) -> IntegrationRegistry:
    timeout = settings.internal_request_timeout_seconds
    def credential(service: str) -> ServiceCredential:
        return ServiceCredential(
            service=service,
            client_id=settings.service_client_id,
            access_token=settings.service_tokens.get(service),
            service_key=settings.service_keys.get(service),
            scopes=required_scopes(service),
        )
    return IntegrationRegistry(
        diddifreeid=DiddiFreeIDAdapter(base_url=settings.diddifreeid_base_url, audience="diddifreeid", timeout=timeout, credential=credential("diddifreeid")),
        diddipay=DiddiPayAdapter(base_url=settings.diddipay_base_url, audience="diddipay", timeout=timeout, credential=credential("diddipay")),
        diddisend=DiddiSendAdapter(base_url=settings.diddisend_base_url, audience="diddisend", timeout=timeout, credential=credential("diddisend")),
        diddifiles=DiddiFilesAdapter(base_url=settings.diddifiles_base_url, audience="diddifiles", timeout=timeout, credential=credential("diddifiles")),
        diddirewards=DiddiRewardsAdapter(base_url=settings.diddirewards_base_url, audience="diddirewards", timeout=timeout, credential=credential("diddirewards")),
        diddicomms=DiddiCommsAdapter(base_url=settings.diddicomms_base_url, audience="diddicomms", timeout=timeout, credential=credential("diddicomms")),
        diddisupport=DiddiSupportAdapter(base_url=settings.diddisupport_base_url, audience="diddisupport", timeout=timeout, credential=credential("diddisupport")),
        diddiobserve=DiddiObserveAdapter(base_url=settings.diddiobserve_base_url, audience="diddiobserve", timeout=timeout, credential=credential("diddiobserve")),
    )
