from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TextDocumentCreateFromTemplateRequest(BaseModel):
    template_id: UUID
    title: str | None = Field(default=None, max_length=255)
    body: str | None = None
    consultation_id: UUID | None = None


class TextDocumentUpdateRequest(BaseModel):
    type: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    consultation_id: UUID | None = None


class TextDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    template_id: UUID | None
    type: str
    title: str
    body: str
    version: int
    created_at: datetime | None
