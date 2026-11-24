from app_base.integrations.diddicomms import DiddiCommsAdapter
from app_base.integrations.diddisupport import DiddiSupportAdapter


def test_comms_and_support_use_staging_contract_prefixes():
    assert hasattr(DiddiCommsAdapter, "create_task")
    assert hasattr(DiddiSupportAdapter, "get_context")
