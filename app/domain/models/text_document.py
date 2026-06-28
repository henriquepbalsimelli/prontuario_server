from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TextDocument:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    type: str
    title: str
    body: str
    consultation_id: UUID | None = None
    template_id: UUID | None = None
    version: int = 1
    created_at: datetime | None = None
