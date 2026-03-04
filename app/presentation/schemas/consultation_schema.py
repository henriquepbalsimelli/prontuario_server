from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConsultationCreateRequest(BaseModel):
    consultation_date: date | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_date: date | None
    chief_complaint: str | None
    physical_exam: str | None
    conduct: str | None
    created_at: datetime | None
