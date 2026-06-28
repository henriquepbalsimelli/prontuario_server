from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class MedicalHistory:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    body: str
    consultation_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
