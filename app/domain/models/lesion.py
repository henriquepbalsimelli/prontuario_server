from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Lesion:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    label: str | None = None
    body_region: str | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    status: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
