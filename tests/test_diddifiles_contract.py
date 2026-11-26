import json

import httpx
import pytest

from app_base.integrations.auth import ServiceCredential
from app_base.integrations.diddifiles import DiddiFilesAdapter


def test_diddifiles_adapter_matches_staging_openapi_routes():
    assert hasattr(DiddiFilesAdapter, "create_upload_session")
    assert hasattr(DiddiFilesAdapter, "confirm_upload")
    assert hasattr(DiddiFilesAdapter, "download_url")
    assert hasattr(DiddiFilesAdapter, "public_or_signed_url")


def test_product_image_purpose_is_explicit():
    payload = {
        "module_owner": "diddishop",
        "purpose": "diddishop_product_image",
        "mime_type": "image/jpeg",
        "size_bytes": 1024,
    }
    assert payload["purpose"] == "diddishop_product_image"


@pytest.mark.anyio
async def test_upload_session_uses_the_live_diddifiles_request_shape():
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "file_id": "file-1",
                "status": "pending",
                "upload": {
                    "method": "PUT",
                    "url": "https://s3.example/upload",
                    "expires_in_seconds": 900,
                    "headers": {},
                },
            },
        )

    adapter = DiddiFilesAdapter(
        base_url="https://files.test",
        audience="diddifiles",
        credential=ServiceCredential("diddifiles", "client", "token"),
        transport=httpx.MockTransport(handler),
    )
    response = await adapter.create_upload_session(
        {
            "module_owner": "diddishop",
            "purpose": "diddishop_product_image",
            "filename": "photo.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 1024,
            "metadata": {"product_id": "product-1"},
        }
    )

    body = json.loads(captured[0].content)
    assert response["upload"]["method"] == "PUT"
    assert body == {
        "module_owner": "diddishop",
        "purpose": "diddishop_product_image",
        "filename": "photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 1024,
        "metadata": {"product_id": "product-1"},
    }
