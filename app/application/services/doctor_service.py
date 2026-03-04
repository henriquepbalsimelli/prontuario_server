from dataclasses import dataclass
from uuid import uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.doctor_repository import DoctorRepository
from app.domain.models.doctor import Doctor
from app.infrastructure.security.password_hashing import hash_password


class DoctorEmailAlreadyExistsError(Exception):
    pass


@dataclass(slots=True)
class CreateDoctorInput:
    name: str
    email: str
    password: str


class DoctorService:
    def __init__(
        self,
        repository: DoctorRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_event_service = audit_event_service

    async def create_doctor(self, payload: CreateDoctorInput) -> Doctor:
        normalized_email = payload.email.strip().lower()
        existing = await self.repository.get_by_email(email=normalized_email)
        if existing is not None:
            raise DoctorEmailAlreadyExistsError("Doctor email already exists")

        doctor = Doctor(
            id=uuid4(),
            name=payload.name.strip(),
            email=normalized_email,
            password_hash=hash_password(payload.password),
        )
        created = await self.repository.create(doctor=doctor)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=created.id,
                entity_type="doctor",
                entity_id=created.id,
                action="create",
                event_type="DoctorCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created
