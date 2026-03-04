from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    active_principle: str | None = Field(default=None, max_length=255)
    form: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    active_principle: str | None
    form: str | None
    notes: str | None
