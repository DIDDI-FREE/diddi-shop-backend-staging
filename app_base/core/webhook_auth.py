import hashlib
import hmac

from fastapi import HTTPException, Request


async def require_webhook_signature(
    request: Request,
    secret: str,
    *,
    header_name: str = "X-Webhook-Signature",
    timestamp_header: str | None = "X-Webhook-Timestamp",
) -> None:
    """Validate an HMAC signature over the exact request body bytes.

    Providers use different signature header names. The default remains the
    generic DiddiShop contract used by legacy callbacks; integrations should
    pass their provider-specific header explicitly.
    """
    if request.app.state.settings.environment == "development":
        return
    if not secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    signature = request.headers.get(header_name)
    timestamp = request.headers.get(timestamp_header, "") if timestamp_header else ""
    if not signature:
        raise HTTPException(status_code=401, detail="Webhook signature required")
    body = await request.body()
    signed = timestamp.encode() + b"." + body if timestamp else body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature.removeprefix("sha256="), expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
