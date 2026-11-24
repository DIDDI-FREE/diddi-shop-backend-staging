import hashlib
import hmac

from fastapi import HTTPException, Request


async def require_webhook_signature(request: Request, secret: str) -> None:
    """Validate the shared-secret signature used by external callbacks."""
    if request.app.state.settings.environment == "development":
        return
    if not secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    signature = request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp", "")
    if not signature:
        raise HTTPException(status_code=401, detail="Webhook signature required")
    body = await request.body()
    signed = timestamp.encode() + b"." + body if timestamp else body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature.removeprefix("sha256="), expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
