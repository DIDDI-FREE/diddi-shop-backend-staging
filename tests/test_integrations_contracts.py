from app_base.integrations.diddisend import DiddiSendAdapter
from app_base.shared_kernel.contracts.delivery import DeliveryRequest


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
        financial_breakdown={"version": "1", "currency": "XOF", "delivery_fee": "1500"},
    )
    payload = request.model_dump()
    assert payload["origin_module"] == "diddishop"
    assert payload["order_reference"] == "shop-order:ord-1"
    assert payload["prepaid_by_origin"] is True
    assert payload["financial_breakdown"]["currency"] == "XOF"


def test_diddisend_adapter_exposes_only_delivery_boundary():
    assert hasattr(DiddiSendAdapter, "create_delivery")
    assert hasattr(DiddiSendAdapter, "cancel_delivery")
    assert not hasattr(DiddiSendAdapter, "assign_courier")


def test_diddisend_delivery_request_contains_prepaid_origin_and_recipient_identity():
    request = DeliveryRequest(
        order_reference="shop-order:ord-1",
        idempotency_key="shop:create-delivery:ord-1:1",
        sender_user_id="seller-1",
        customer_user_id="buyer-1",
        recipient_user_id="buyer-1",
        recipient_name="Buyer",
        recipient_phone="690000000",
        pickup_location={"lat": 3.86, "lng": 11.52, "address": "Pickup"},
        pickup_address="Pickup",
        dropoff_location={"lat": 3.87, "lng": 11.53, "address": "Dropoff"},
        dropoff_address="Dropoff",
        package={
            "label": "Order",
            "description": "Goods",
            "category": "physical_goods",
            "declared_value": 1500,
        },
        quoted_price="1500",
    )
    assert request.prepaid_by_origin is True
    assert request.recipient_user_id == "buyer-1"
