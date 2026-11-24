from fastapi import APIRouter

router = APIRouter(prefix="/v1/admin/shop", tags=["admin-shop"])


@router.get("/capabilities")
async def capabilities():
    return {
        "service": "diddishop",
        "owner": "diddi-shop",
        "commands": ["read_order", "read_claim", "decide_claim", "retry_external_operation"],
        "note": "Backoffice calls these routes through a scoped adapter and records its own operator audit.",
    }
