from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    birth_date: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = None


class PatientUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    birth_date: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    name: str
    birth_date: date | None
    gender: str | None
    phone: str | None
    notes: str | None
    created_at: datetime | None
