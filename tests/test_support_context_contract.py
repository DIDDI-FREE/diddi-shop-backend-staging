from app_base.core.api_contracts import support_context_stub_response


def test_support_context_uses_standard_envelope():
    response = support_context_stub_response("order-1")

    assert response["protocol"] == "diddi.context.v1"
    assert response["origin_service"] == "diddishop"
    assert response["resource_type"] == "order"
    assert response["resource_id"] == "order-1"
    assert response["redacted_fields"] == []
    assert response["data"]["order"] == {"id": "order-1"}
    assert response["fetched_at"].tzinfo is not None

