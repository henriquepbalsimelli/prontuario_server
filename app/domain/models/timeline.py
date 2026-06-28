from dataclasses import dataclass
from datetime import date
from uuid import UUID

TIMELINE_SOURCE_CONSULTATION = "consultation"
TIMELINE_SOURCE_PROCEDURE = "procedure"


@dataclass(slots=True)
class TimelineEvent:
    id: str
    source_type: str
    occurred_at: date | None
    title: str
    summary: str | None
    consultation_id: UUID | None
    source_id: UUID
