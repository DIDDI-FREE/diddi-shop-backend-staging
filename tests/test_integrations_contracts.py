from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryCommand, DeliveryRequest


def test_diddisend_request_matches_food_style_contract():
    request = DeliveryRequest(
        order_reference="shop-order:ord-1",
        idempotency_key="shop:create-delivery:ord-1:1",
        sender_user_id="diddishop-system",
        customer_user_id="user-1",
        recipient_name="Buyer",
        recipient_phone="690000000",
        pickup_location={"lat": 3.86, "lng": 11.52},
        pickup_address="Seller pickup",
        dropoff_location={"lat": 3.87, "lng": 11.53},
        dropoff_address="Buyer dropoff",
        package={"label": "DiddiShop order", "category": "physical_goods"},
        quoted_price="1500",
        financial_breakdown={"version": "1", "currency": "XAF", "delivery_fee": "1500"},
    )
    payload = request.model_dump()
    assert payload["origin_module"] == "diddishop"
    assert payload["order_reference"] == "shop-order:ord-1"
    assert payload["prepaid_by_origin"] is True
    assert payload["financial_breakdown"]["currency"] == "XAF"


def test_diddisend_adapter_exposes_only_delivery_boundary():
    assert hasattr(DiddiSendAdapter, "create_delivery")
    assert hasattr(DiddiSendAdapter, "cancel_delivery")
    assert not hasattr(DiddiSendAdapter, "assign_courier")
