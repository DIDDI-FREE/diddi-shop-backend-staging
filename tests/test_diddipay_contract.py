from app_base.integrations.diddipay import DiddiPayAdapter


def test_diddipay_adapter_exposes_payment_lifecycle_without_card_data():
    assert hasattr(DiddiPayAdapter, "create_payment_intent")
    assert hasattr(DiddiPayAdapter, "cancel_payment_intent")
    assert hasattr(DiddiPayAdapter, "refund")
    assert not hasattr(DiddiPayAdapter, "charge_card")
