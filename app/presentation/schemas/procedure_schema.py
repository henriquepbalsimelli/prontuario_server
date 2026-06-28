from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcedureCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    procedure_date: date | None = None
    description: str | None = None
    notes: str | None = None
    consultation_id: UUID | None = None


class ProcedureUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    procedure_date: date | None = None
    description: str | None = None
    notes: str | None = None
    consultation_id: UUID | None = None


class ProcedureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    procedure_date: date | None
    title: str
    description: str | None
    notes: str | None
    created_at: datetime | None
