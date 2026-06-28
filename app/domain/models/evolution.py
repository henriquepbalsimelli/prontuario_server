from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Evolution:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    origin_type: str
    content: str
    occurred_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
