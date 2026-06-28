from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


EvolutionOriginType = Literal[
    "consultation",
    "inpatient_visit",
    "exam_review",
    "phone_contact",
    "telemedicine",
    "procedure",
    "hospital_event",
    "multidisciplinary_discussion",
    "other",
]


class EvolutionCreateRequest(BaseModel):
    consultation_id: UUID | None = None
    origin_type: EvolutionOriginType
    content: str = Field(min_length=1)
    occurred_at: datetime


class EvolutionUpdateRequest(BaseModel):
    consultation_id: UUID | None = None
    origin_type: EvolutionOriginType
    content: str = Field(min_length=1)
    occurred_at: datetime


class EvolutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    origin_type: str
    content: str
    occurred_at: datetime
    created_at: datetime | None
    updated_at: datetime | None
