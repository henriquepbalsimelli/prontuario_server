from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.exam_repository import ExamRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.exam import EXAM_STATUS_PERFORMED, EXAM_STATUS_REQUESTED, EXAM_STATUS_REVIEWED, Exam


class ExamPatientNotFoundError(Exception):
    pass


class ExamNotFoundError(Exception):
    pass


class ExamValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateExamInput:
    name: str
    type: str | None = None
    exam_date: date | None = None
    status: str = EXAM_STATUS_REQUESTED
    result_notes: str | None = None
    consultation_id: UUID | None = None


@dataclass(slots=True)
class UpdateExamInput:
    name: str
    type: str | None = None
    exam_date: date | None = None
    status: str = EXAM_STATUS_REQUESTED
    result_notes: str | None = None
    consultation_id: UUID | None = None


class ExamService:
    ALLOWED_STATUSES = {EXAM_STATUS_REQUESTED, EXAM_STATUS_PERFORMED, EXAM_STATUS_REVIEWED}

    def __init__(
        self,
        repository: ExamRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.audit_event_service = audit_event_service

    async def list_exams(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Exam]:
        await self._require_patient(doctor_id, patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, consultation_id)
        normalized_status = self._normalize_status(status) if status is not None else None
        return await self.repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status=normalized_status,
            consultation_id=consultation_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_exam(self, doctor_id: UUID, exam_id: UUID) -> Exam:
        exam = await self.repository.get_by_id(doctor_id=doctor_id, exam_id=exam_id)
        if exam is None:
            raise ExamNotFoundError("Exam not found")
        return exam

    async def create_exam(self, doctor_id: UUID, patient_id: UUID, payload: CreateExamInput) -> Exam:
        await self._require_patient(doctor_id, patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, payload.consultation_id)
        exam = Exam(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
            name=self._normalize_name(payload.name),
            type=payload.type,
            exam_date=payload.exam_date,
            status=self._normalize_status(payload.status),
            result_notes=payload.result_notes,
        )
        created = await self.repository.create(exam)
        await self._audit("create", "ExamCreated", doctor_id, created.id, None, created)
        return created

    async def update_exam(self, doctor_id: UUID, exam_id: UUID, payload: UpdateExamInput) -> Exam:
        existing = await self.get_exam(doctor_id, exam_id)
        await self._validate_consultation_reference(doctor_id, existing.patient_id, payload.consultation_id)
        updated = Exam(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
            name=self._normalize_name(payload.name),
            type=payload.type,
            exam_date=payload.exam_date,
            status=self._normalize_status(payload.status),
            result_notes=payload.result_notes,
            created_at=existing.created_at,
        )
        saved = await self.repository.update(updated)
        await self._audit("update", "ExamUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_exam(self, doctor_id: UUID, exam_id: UUID) -> None:
        existing = await self.get_exam(doctor_id, exam_id)
        deleted = await self.repository.delete(doctor_id=doctor_id, exam_id=exam_id)
        if not deleted:
            raise ExamNotFoundError("Exam not found")
        await self._audit("delete", "ExamDeleted", doctor_id, exam_id, existing, None)

    async def _require_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise ExamPatientNotFoundError("Patient not found")

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
            raise ExamValidationError("Consultation not found for patient")

    def _normalize_name(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ExamValidationError("Name is required")
        return normalized

    def _normalize_status(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in self.ALLOWED_STATUSES:
            raise ExamValidationError("Invalid status")
        return normalized

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="exam",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
