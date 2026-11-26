from pydantic import BaseModel, Field, field_validator

from app_base.modules.catalog.domain import ALLOWED_PRODUCT_IMAGE_MIME_TYPES, MAX_PRODUCT_PHOTOS


class CreateProductRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    price_minor: int = Field(ge=0)
    stock: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=120)
    photo_file_ids: list[str] = Field(default_factory=list, max_length=MAX_PRODUCT_PHOTOS)


class UpdateProductRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price_minor: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, min_length=1, max_length=120)


class AttachProductPhotoRequest(BaseModel):
    file_id: str = Field(min_length=1, max_length=200)


class CreatePhotoUploadSessionRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        if value not in ALLOWED_PRODUCT_IMAGE_MIME_TYPES:
            raise ValueError("content_type must be image/jpeg, image/png or image/webp")
        return value
