from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ExamStatus = Literal["requested", "performed", "reviewed"]


class ExamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str | None = Field(default=None, max_length=255)
    exam_date: date | None = None
    status: ExamStatus = "requested"
    result_notes: str | None = None
    consultation_id: UUID | None = None


class ExamUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str | None = Field(default=None, max_length=255)
    exam_date: date | None = None
    status: ExamStatus = "requested"
    result_notes: str | None = None
    consultation_id: UUID | None = None


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    name: str
    type: str | None
    exam_date: date | None
    status: str
    result_notes: str | None
    created_at: datetime | None
