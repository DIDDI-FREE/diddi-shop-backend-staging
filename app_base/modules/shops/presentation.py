from pydantic import BaseModel, Field


class CreateShopRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    pickup_address: str = Field(min_length=1, max_length=500)
    pickup_latitude: float
    pickup_longitude: float
