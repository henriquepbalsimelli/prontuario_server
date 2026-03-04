from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Image:
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    consultation_id: UUID | None
    s3_key: str
    type: str | None = None
    body_region: str | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    upload_status: str = "pending"
    uploaded_at: datetime | None = None
    file_size_bytes: int | None = None
    etag: str | None = None
    created_at: datetime | None = None
