from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

EXAM_STATUS_REQUESTED = "requested"
EXAM_STATUS_PERFORMED = "performed"
EXAM_STATUS_REVIEWED = "reviewed"


@dataclass(slots=True)
class Exam:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None = None
    name: str = ""
    type: str | None = None
    exam_date: date | None = None
    status: str = EXAM_STATUS_REQUESTED
    result_notes: str | None = None
    created_at: datetime | None = None
