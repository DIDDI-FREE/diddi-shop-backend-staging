from pydantic import BaseModel, Field


class AddCartLineRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
