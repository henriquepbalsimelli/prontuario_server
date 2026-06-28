from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True)
class Patient:
    id: UUID
    doctor_id: UUID
    name: str
    birth_date: date | None = None
    gender: str | None = None
    phone: str | None = None
    medical_history: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
