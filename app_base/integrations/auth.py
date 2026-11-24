from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCredential:
    service: str
    client_id: str
    access_token: str | None = None
    service_key: str | None = None


def s2s_headers(credential: ServiceCredential, *, origin_service: str = "diddishop", user_id: str = "diddishop-system", request_id: str | None = None, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"X-Origin-Service": origin_service, "X-User-ID": user_id}
    if credential.access_token:
        headers["Authorization"] = f"Bearer {credential.access_token}"
    elif credential.service_key:
        headers["X-Client-ID"] = credential.client_id
        headers["X-Service-Key"] = credential.service_key
    else:
        raise ValueError(f"No S2S credential configured for {credential.service}")
    if request_id:
        headers["X-Request-ID"] = request_id
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers
