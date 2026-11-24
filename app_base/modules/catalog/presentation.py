from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    price_minor: int = Field(ge=0)
    stock: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=120)
    photo_file_ids: list[str] = Field(default_factory=list)
