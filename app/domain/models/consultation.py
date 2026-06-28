from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

CONSULTATION_STATUS_SCHEDULED = "scheduled"
CONSULTATION_STATUS_COMPLETED = "completed"
CONSULTATION_STATUS_CANCELLED = "cancelled"


@dataclass(slots=True)
class Consultation:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_date: date | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    status: str | None = None
    diagnosis: str | None = None
    notes: str | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None
    created_at: datetime | None = None
