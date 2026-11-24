ADMIN_MANIFEST = {
    "service": "diddishop",
    "version": "v1",
    "resources": ["orders", "payments", "deliveries", "claims", "audit"],
    "commands": [
        {"name": "read_order", "method": "GET", "path": "/v1/admin/shop/orders/{order_id}"},
        {"name": "decide_claim", "method": "POST", "path": "/v1/admin/shop/claims/{claim_id}/decision"},
    ],
    "ownership": {"delivery": "diddisend", "payment": "diddipay", "campaigns": "diddirewards"},
}
