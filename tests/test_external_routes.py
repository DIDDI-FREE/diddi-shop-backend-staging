import pytest

from app_base.integrations.diddicomms import DiddiCommsAdapter
from app_base.integrations.diddisupport import DiddiSupportAdapter


def test_comms_and_support_use_staging_contract_prefixes():
    assert hasattr(DiddiCommsAdapter, "open_conversation")
    assert not hasattr(DiddiCommsAdapter, "create_task")
    assert hasattr(DiddiSupportAdapter, "get_context")


@pytest.mark.asyncio
async def test_comms_conversation_route_has_no_json_body(monkeypatch):
    adapter = DiddiCommsAdapter(base_url="https://comms.test", audience="diddicomms")
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "conversation-1"}

    async def request(method, path, **kwargs):
        captured.update(method=method, path=path, kwargs=kwargs)
        return Response()

    monkeypatch.setattr(adapter, "request", request)
    result = await adapter.open_conversation(
        "diddishop",
        "order",
        "11111111-1111-1111-1111-111111111111",
        "shop:conversation:order-1:1",
    )

    assert result["id"] == "conversation-1"
    assert captured["path"] == "/comms/v1/tasks/diddishop/order/11111111-1111-1111-1111-111111111111/conversation"
    assert captured["kwargs"]["headers"] == {"Idempotency-Key": "shop:conversation:order-1:1"}
    assert "json" not in captured["kwargs"]
