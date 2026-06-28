from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.interfaces.procedure_repository import ProcedureRepository
from app.domain.models.procedure import Procedure


class ProcedurePatientNotFoundError(Exception):
    pass


class ProcedureNotFoundError(Exception):
    pass


class ProcedureValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateProcedureInput:
    title: str
    procedure_date: date | None = None
    description: str | None = None
    notes: str | None = None
    consultation_id: UUID | None = None


@dataclass(slots=True)
class UpdateProcedureInput:
    title: str
    procedure_date: date | None = None
    description: str | None = None
    notes: str | None = None
    consultation_id: UUID | None = None


class ProcedureService:
    def __init__(
        self,
        repository: ProcedureRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.audit_event_service = audit_event_service

    async def list_procedures(self, doctor_id: UUID, patient_id: UUID) -> list[Procedure]:
        await self._require_patient(doctor_id, patient_id)
        return await self.repository.list_by_patient(doctor_id=doctor_id, patient_id=patient_id)

    async def get_procedure(self, doctor_id: UUID, procedure_id: UUID) -> Procedure:
        procedure = await self.repository.get_by_id(doctor_id=doctor_id, procedure_id=procedure_id)
        if procedure is None:
            raise ProcedureNotFoundError("Procedure not found")
        return procedure

    async def create_procedure(self, doctor_id: UUID, patient_id: UUID, payload: CreateProcedureInput) -> Procedure:
        await self._require_patient(doctor_id, patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, payload.consultation_id)
        procedure = Procedure(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
            procedure_date=payload.procedure_date,
            title=self._normalize_title(payload.title),
            description=payload.description,
            notes=payload.notes,
        )
        created = await self.repository.create(procedure)
        await self._audit("create", "ProcedureCreated", doctor_id, created.id, None, created)
        return created

    async def update_procedure(self, doctor_id: UUID, procedure_id: UUID, payload: UpdateProcedureInput) -> Procedure:
        existing = await self.get_procedure(doctor_id, procedure_id)
        await self._validate_consultation_reference(doctor_id, existing.patient_id, payload.consultation_id)
        updated = Procedure(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
            procedure_date=payload.procedure_date,
            title=self._normalize_title(payload.title),
            description=payload.description,
            notes=payload.notes,
            created_at=existing.created_at,
        )
        saved = await self.repository.update(updated)
        await self._audit("update", "ProcedureUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_procedure(self, doctor_id: UUID, procedure_id: UUID) -> None:
        existing = await self.get_procedure(doctor_id, procedure_id)
        deleted = await self.repository.delete(doctor_id=doctor_id, procedure_id=procedure_id)
        if not deleted:
            raise ProcedureNotFoundError("Procedure not found")
        await self._audit("delete", "ProcedureDeleted", doctor_id, procedure_id, existing, None)

    async def _require_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise ProcedurePatientNotFoundError("Patient not found")

    async def _validate_consultation_reference(self, doctor_id: UUID, patient_id: UUID, consultation_id: UUID | None) -> None:
        if consultation_id is None:
            return
        consultation = await self.consultation_repository.get_by_id(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            patient_id=patient_id,
        )
        if consultation is None:
            raise ProcedureValidationError("Consultation not found for patient")

    def _normalize_title(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ProcedureValidationError("Title is required")
        return normalized

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="procedure",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
