from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicalHistoryCreateRequest(BaseModel):
    body: str = Field(min_length=1)
    consultation_id: UUID | None = None


class MedicalHistoryUpdateRequest(BaseModel):
    body: str = Field(min_length=1)
    consultation_id: UUID | None = None


class MedicalHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    body: str
    created_at: datetime | None
    updated_at: datetime | None
