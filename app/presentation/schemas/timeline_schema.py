from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    occurred_at: date | None
    title: str
    summary: str | None
    consultation_id: UUID | None
    source_id: UUID
