from dataclasses import dataclass

from app_base.core.settings import Settings
from app_base.integrations.diddicomms import DiddiCommsAdapter
from app_base.integrations.diddifiles import DiddiFilesAdapter
from app_base.integrations.diddifreeid import DiddiFreeIDAdapter
from app_base.integrations.diddimap import DiddiMapAdapter
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
    diddimap: DiddiMapAdapter
    diddifiles: DiddiFilesAdapter
    diddirewards: DiddiRewardsAdapter
    diddicomms: DiddiCommsAdapter
    diddisupport: DiddiSupportAdapter
    diddiobserve: DiddiObserveAdapter


def build_integrations(settings: Settings) -> IntegrationRegistry:
    timeout = settings.internal_request_timeout_seconds
    return IntegrationRegistry(
        diddifreeid=DiddiFreeIDAdapter(base_url=settings.diddifreeid_base_url, audience="diddifreeid", timeout=timeout),
        diddipay=DiddiPayAdapter(base_url=settings.diddipay_base_url, audience="diddipay", timeout=timeout),
        diddisend=DiddiSendAdapter(base_url=settings.diddisend_base_url, audience="diddisend", timeout=timeout),
        diddimap=DiddiMapAdapter(base_url=settings.diddimap_base_url, audience="diddimap", timeout=timeout),
        diddifiles=DiddiFilesAdapter(base_url=settings.diddifiles_base_url, audience="diddifiles", timeout=timeout),
        diddirewards=DiddiRewardsAdapter(base_url=settings.diddirewards_base_url, audience="diddirewards", timeout=timeout),
        diddicomms=DiddiCommsAdapter(base_url=settings.diddicomms_base_url, audience="diddicomms", timeout=timeout),
        diddisupport=DiddiSupportAdapter(base_url=settings.diddisupport_base_url, audience="diddisupport", timeout=timeout),
        diddiobserve=DiddiObserveAdapter(base_url=settings.diddiobserve_base_url, audience="diddiobserve", timeout=timeout),
    )
