from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LesionCreateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    body_region: str | None = Field(default=None, max_length=120)
    coord_x: float | None = None
    coord_y: float | None = None
    status: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class LesionUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    body_region: str | None = Field(default=None, max_length=120)
    coord_x: float | None = None
    coord_y: float | None = None
    status: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class LesionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    label: str | None
    body_region: str | None
    coord_x: float | None
    coord_y: float | None
    status: str | None
    notes: str | None
    created_at: datetime | None
