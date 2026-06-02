from typing import Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None


class DoctorDashboardPreferencesRequest(BaseModel):
    item_order: list[str] = Field(default_factory=list)


class DoctorPreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    dashboard: DoctorDashboardPreferencesRequest = Field(
        default_factory=DoctorDashboardPreferencesRequest
    )
    theme: str = Field(min_length=1, max_length=100)


class DoctorPreferencesResponse(BaseModel):
    doctor_id: UUID
    preferences: dict[str, Any]
