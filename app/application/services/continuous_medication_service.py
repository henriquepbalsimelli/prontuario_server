from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.continuous_medication_repository import ContinuousMedicationRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.continuous_medication import (
    CONTINUOUS_MEDICATION_STATUS_ACTIVE,
    CONTINUOUS_MEDICATION_STATUS_INACTIVE,
    ContinuousMedication,
)


class ContinuousMedicationPatientNotFoundError(Exception):
    pass


class ContinuousMedicationNotFoundError(Exception):
    pass


class ContinuousMedicationValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateContinuousMedicationInput:
    name: str
    consultation_id: UUID | None = None
    dosage: str | None = None
    notes: str | None = None
    status: str = CONTINUOUS_MEDICATION_STATUS_ACTIVE


@dataclass(slots=True)
class UpdateContinuousMedicationInput:
    name: str
    consultation_id: UUID | None = None
    dosage: str | None = None
    notes: str | None = None
    status: str = CONTINUOUS_MEDICATION_STATUS_ACTIVE


class ContinuousMedicationService:
    ALLOWED_STATUSES = {
        CONTINUOUS_MEDICATION_STATUS_ACTIVE,
        CONTINUOUS_MEDICATION_STATUS_INACTIVE,
    }

    def __init__(
        self,
        repository: ContinuousMedicationRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.audit_event_service = audit_event_service

    async def list_medications(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
    ) -> list[ContinuousMedication]:
        await self._require_patient(doctor_id=doctor_id, patient_id=patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, consultation_id)
        normalized_status = self._normalize_status(status) if status is not None else None
        return await self.repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status=normalized_status,
            consultation_id=consultation_id,
        )

    async def create_medication(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateContinuousMedicationInput,
    ) -> ContinuousMedication:
        await self._require_patient(doctor_id=doctor_id, patient_id=patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, payload.consultation_id)
        medication = ContinuousMedication(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            name=self._normalize_name(payload.name),
            consultation_id=payload.consultation_id,
            dosage=payload.dosage,
            notes=payload.notes,
            status=self._normalize_status(payload.status),
        )
        created = await self.repository.create(medication)
        await self._audit("create", "ContinuousMedicationCreated", doctor_id, created.id, None, created)
        return created

    async def update_medication(
        self,
        doctor_id: UUID,
        medication_id: UUID,
        payload: UpdateContinuousMedicationInput,
    ) -> ContinuousMedication:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, medication_id=medication_id)
        if existing is None:
            raise ContinuousMedicationNotFoundError("Continuous medication not found")
        await self._validate_consultation_reference(doctor_id, existing.patient_id, payload.consultation_id)
        updated = ContinuousMedication(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            name=self._normalize_name(payload.name),
            consultation_id=payload.consultation_id,
            dosage=payload.dosage,
            notes=payload.notes,
            status=self._normalize_status(payload.status),
            created_at=existing.created_at,
        )
        saved = await self.repository.update(updated)
        await self._audit("update", "ContinuousMedicationUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_medication(self, doctor_id: UUID, medication_id: UUID) -> None:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, medication_id=medication_id)
        if existing is None:
            raise ContinuousMedicationNotFoundError("Continuous medication not found")
        deleted = await self.repository.delete(doctor_id=doctor_id, medication_id=medication_id)
        if not deleted:
            raise ContinuousMedicationNotFoundError("Continuous medication not found")
        await self._audit("delete", "ContinuousMedicationDeleted", doctor_id, medication_id, existing, None)

    async def _require_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise ContinuousMedicationPatientNotFoundError("Patient not found")

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
            raise ContinuousMedicationValidationError("Consultation not found for patient")

    def _normalize_name(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ContinuousMedicationValidationError("Name is required")
        return normalized

    def _normalize_status(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in self.ALLOWED_STATUSES:
            raise ContinuousMedicationValidationError("Invalid status")
        return normalized

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="continuous_medication",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
