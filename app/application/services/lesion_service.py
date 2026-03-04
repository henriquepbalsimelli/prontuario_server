from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.lesion_repository import LesionRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.lesion import Lesion


class LesionPatientNotFoundError(Exception):
    pass


class LesionNotFoundError(Exception):
    pass


@dataclass(slots=True)
class CreateLesionInput:
    label: str | None = None
    body_region: str | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    status: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class UpdateLesionInput:
    label: str | None = None
    body_region: str | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    status: str | None = None
    notes: str | None = None


class LesionService:
    def __init__(
        self,
        lesion_repository: LesionRepository,
        patient_repository: PatientRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.lesion_repository = lesion_repository
        self.patient_repository = patient_repository
        self.audit_event_service = audit_event_service

    async def list_lesions(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Lesion]:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise LesionPatientNotFoundError("Patient not found")

        return await self.lesion_repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )

    async def create_lesion(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateLesionInput,
    ) -> Lesion:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise LesionPatientNotFoundError("Patient not found")

        lesion = Lesion(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            label=payload.label,
            body_region=payload.body_region,
            coord_x=payload.coord_x,
            coord_y=payload.coord_y,
            status=payload.status,
            notes=payload.notes,
        )
        created = await self.lesion_repository.create(lesion=lesion)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="lesion",
                entity_id=created.id,
                action="create",
                event_type="LesionCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created

    async def update_lesion(
        self,
        doctor_id: UUID,
        lesion_id: UUID,
        payload: UpdateLesionInput,
    ) -> Lesion:
        existing = await self.lesion_repository.get_by_id(
            doctor_id=doctor_id,
            lesion_id=lesion_id,
        )
        if existing is None:
            raise LesionNotFoundError("Lesion not found")

        updated = Lesion(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            label=payload.label,
            body_region=payload.body_region,
            coord_x=payload.coord_x,
            coord_y=payload.coord_y,
            status=payload.status,
            notes=payload.notes,
            created_at=existing.created_at,
        )
        saved = await self.lesion_repository.update(lesion=updated)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="lesion",
                entity_id=saved.id,
                action="update",
                event_type="LesionUpdated",
                before_state=to_audit_dict(existing),
                after_state=to_audit_dict(saved),
            )
        return saved
