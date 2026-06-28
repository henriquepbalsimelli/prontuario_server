from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ContinuousMedicationStatus = Literal["active", "inactive"]


class ContinuousMedicationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    consultation_id: UUID | None = None
    dosage: str | None = None
    notes: str | None = None
    status: ContinuousMedicationStatus = "active"


class ContinuousMedicationUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    consultation_id: UUID | None = None
    dosage: str | None = None
    notes: str | None = None
    status: ContinuousMedicationStatus = "active"


class ContinuousMedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    name: str
    dosage: str | None
    notes: str | None
    status: str
    created_at: datetime | None
