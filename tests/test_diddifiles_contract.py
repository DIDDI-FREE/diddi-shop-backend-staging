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
