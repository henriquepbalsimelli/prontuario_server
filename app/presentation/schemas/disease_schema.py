from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiseaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cid10: str | None = Field(default=None, max_length=20)
    description: str | None = None


class DiseaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    cid10: str | None
    description: str | None
