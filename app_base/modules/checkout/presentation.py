from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    idempotency_key: str
