from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

CONTINUOUS_MEDICATION_STATUS_ACTIVE = "active"
CONTINUOUS_MEDICATION_STATUS_INACTIVE = "inactive"


@dataclass(slots=True)
class ContinuousMedication:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    name: str
    consultation_id: UUID | None = None
    dosage: str | None = None
    notes: str | None = None
    status: str = CONTINUOUS_MEDICATION_STATUS_ACTIVE
    created_at: datetime | None = None
