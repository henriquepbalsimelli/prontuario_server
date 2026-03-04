from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True)
class Consultation:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_date: date | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None
    created_at: datetime | None = None
