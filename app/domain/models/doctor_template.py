from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

DOCTOR_TEMPLATE_TYPE_CONDUCT = "conduct"
DOCTOR_TEMPLATE_TYPE_PRESCRIPTION = "prescription"
DOCTOR_TEMPLATE_TYPE_GENERAL = "general"


@dataclass(slots=True)
class DoctorTemplate:
    id: UUID
    doctor_id: UUID
    title: str
    type: str
    body: str
    created_at: datetime | None = None
