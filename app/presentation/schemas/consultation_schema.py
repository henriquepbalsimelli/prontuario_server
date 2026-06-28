from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ConsultationStatus = Literal["scheduled", "completed", "cancelled"]


def _validate_timezone_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include timezone")
    return value


class ConsultationContinuousMedicationRequest(BaseModel):
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    dosage: str | None = None
    notes: str | None = None
    active: bool = True


class ConsultationCreateRequest(BaseModel):
    consultation_date: date | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    status: ConsultationStatus | None = None
    diagnosis: str | None = None
    notes: str | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None
    medical_history_body: str | None = None
    continuous_medications: list[ConsultationContinuousMedicationRequest] = Field(
        default_factory=list
    )

    _validate_scheduled_start_at = field_validator("scheduled_start_at")(_validate_timezone_aware)
    _validate_scheduled_end_at = field_validator("scheduled_end_at")(_validate_timezone_aware)


class ConsultationUpdateRequest(BaseModel):
    consultation_date: date | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    status: ConsultationStatus | None = None
    diagnosis: str | None = None
    notes: str | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None
    medical_history_body: str | None = None
    continuous_medications: list[ConsultationContinuousMedicationRequest] = Field(
        default_factory=list
    )

    _validate_scheduled_start_at = field_validator("scheduled_start_at")(_validate_timezone_aware)
    _validate_scheduled_end_at = field_validator("scheduled_end_at")(_validate_timezone_aware)


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_date: date | None
    scheduled_start_at: datetime | None
    scheduled_end_at: datetime | None
    status: str | None
    diagnosis: str | None
    notes: str | None
    chief_complaint: str | None
    physical_exam: str | None
    conduct: str | None
    created_at: datetime | None
