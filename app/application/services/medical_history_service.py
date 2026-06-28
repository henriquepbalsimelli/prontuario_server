from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.medical_history_repository import MedicalHistoryRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.medical_history import MedicalHistory


class MedicalHistoryPatientNotFoundError(Exception):
    pass


class MedicalHistoryNotFoundError(Exception):
    pass


class MedicalHistoryValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateMedicalHistoryInput:
    body: str
    consultation_id: UUID | None = None


@dataclass(slots=True)
class UpdateMedicalHistoryInput:
    body: str
    consultation_id: UUID | None = None


class MedicalHistoryService:
    def __init__(
        self,
        repository: MedicalHistoryRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.audit_event_service = audit_event_service

    async def list_histories(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID | None = None,
    ) -> list[MedicalHistory]:
        await self._require_patient(doctor_id=doctor_id, patient_id=patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, consultation_id)
        return await self.repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=consultation_id,
        )

    async def create_history(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateMedicalHistoryInput,
    ) -> MedicalHistory:
        await self._require_patient(doctor_id=doctor_id, patient_id=patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, payload.consultation_id)
        history = MedicalHistory(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
            body=self._normalize_body(payload.body),
        )
        created = await self.repository.create(history)
        await self._audit("create", "MedicalHistoryCreated", doctor_id, created.id, None, created)
        return created

    async def update_history(
        self,
        doctor_id: UUID,
        history_id: UUID,
        payload: UpdateMedicalHistoryInput,
    ) -> MedicalHistory:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, history_id=history_id)
        if existing is None:
            raise MedicalHistoryNotFoundError("Medical history not found")
        await self._validate_consultation_reference(doctor_id, existing.patient_id, payload.consultation_id)
        updated = MedicalHistory(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
            body=self._normalize_body(payload.body),
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = await self.repository.update(updated)
        await self._audit("update", "MedicalHistoryUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_history(self, doctor_id: UUID, history_id: UUID) -> None:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, history_id=history_id)
        if existing is None:
            raise MedicalHistoryNotFoundError("Medical history not found")
        deleted = await self.repository.delete(doctor_id=doctor_id, history_id=history_id)
        if not deleted:
            raise MedicalHistoryNotFoundError("Medical history not found")
        await self._audit("delete", "MedicalHistoryDeleted", doctor_id, history_id, existing, None)

    async def get_latest_history(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> MedicalHistory | None:
        await self._require_patient(doctor_id=doctor_id, patient_id=patient_id)
        return await self.repository.get_latest_for_patient(doctor_id=doctor_id, patient_id=patient_id)

    async def _require_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise MedicalHistoryPatientNotFoundError("Patient not found")

    async def _validate_consultation_reference(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID | None,
    ) -> None:
        if consultation_id is None:
            return
        consultation = await self.consultation_repository.get_by_id(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            patient_id=patient_id,
        )
        if consultation is None:
            raise MedicalHistoryValidationError("Consultation not found for patient")

    def _normalize_body(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise MedicalHistoryValidationError("Body is required")
        return normalized

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="medical_history",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
