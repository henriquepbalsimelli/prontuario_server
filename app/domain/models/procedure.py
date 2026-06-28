from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True)
class Procedure:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None = None
    procedure_date: date | None = None
    title: str = ""
    description: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
