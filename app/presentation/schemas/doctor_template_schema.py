from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DoctorTemplateType = Literal["conduct", "prescription", "general"]


class DoctorTemplateCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: DoctorTemplateType
    body: str = Field(min_length=1)


class DoctorTemplateUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: DoctorTemplateType
    body: str = Field(min_length=1)


class DoctorTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    title: str
    type: str
    body: str
    created_at: datetime | None
