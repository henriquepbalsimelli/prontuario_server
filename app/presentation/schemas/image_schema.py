from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImagePresignedUrlRequest(BaseModel):
    patient_id: UUID
    consultation_id: UUID | None = None
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    image_type: str | None = Field(default=None, max_length=80)
    body_region: str | None = Field(default=None, max_length=120)
    coord_x: float | None = None
    coord_y: float | None = None


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    s3_key: str
    type: str | None
    body_region: str | None
    coord_x: float | None
    coord_y: float | None
    upload_status: str
    uploaded_at: datetime | None
    file_size_bytes: int | None
    etag: str | None
    created_at: datetime | None


class ImagePresignedUrlResponse(BaseModel):
    image: ImageResponse
    upload_url: str
    method: str
    expires_in: int
    max_upload_size_mb: int


class ImageConfirmUploadResponse(BaseModel):
    image: ImageResponse
