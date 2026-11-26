from app_base.main import app


def test_openapi_declares_frontend_response_schemas():
    paths = app.openapi()["paths"]

    expected = {
        ("GET", "/v1/shops/{shop_id}"): "ShopResponse",
        ("GET", "/v1/shops/mine"): "ShopListResponse",
        ("GET", "/v1/catalog/categories"): "CategoryListResponse",
        ("GET", "/v1/catalog/products"): "ProductListResponse",
        ("GET", "/v1/catalog/products/{product_id}"): "ProductResponse",
        ("GET", "/v1/catalog/products/{product_id}/photos"): "ProductPhotoListResponse",
        ("POST", "/v1/catalog/products/{product_id}/photos/upload-session"): "UploadSessionResponse",
        ("GET", "/v1/cart"): "CartResponse",
        ("PATCH", "/v1/cart/lines/{product_id}"): "CartResponse",
        ("GET", "/v1/orders"): "OrderListResponse",
        ("GET", "/v1/orders/{order_id}"): "OrderResponse",
        ("POST", "/v1/checkouts"): "CheckoutResponse",
    }

    for (method, path), schema in expected.items():
        operation = paths[path][method.lower()]
        response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["$ref"] == f"#/components/schemas/{schema}"


def test_openapi_enumerates_product_statuses_and_xof():
    schemas = app.openapi()["components"]["schemas"]
    product = schemas["ProductResponse"]["properties"]
    assert product["currency"]["const"] == "XOF"
    assert product["status"]["enum"] == ["draft", "published", "paused", "retired"]
