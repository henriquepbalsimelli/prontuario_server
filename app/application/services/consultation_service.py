from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.continuous_medication_repository import ContinuousMedicationRepository
from app.domain.interfaces.evolution_repository import EvolutionRepository
from app.domain.interfaces.medical_history_repository import MedicalHistoryRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.consultation import (
    CONSULTATION_STATUS_CANCELLED,
    CONSULTATION_STATUS_COMPLETED,
    CONSULTATION_STATUS_SCHEDULED,
    Consultation,
)
from app.domain.models.continuous_medication import ContinuousMedication
from app.domain.models.evolution import Evolution
from app.domain.models.medical_history import MedicalHistory


@dataclass(slots=True)
class ConsultationMedicationInput:
    id: UUID | None = None
    name: str = ""
    dosage: str | None = None
    notes: str | None = None
    active: bool = True


class ConsultationPatientNotFoundError(Exception):
    pass


class ConsultationNotFoundError(Exception):
    pass


class ConsultationValidationError(Exception):
    pass


class ConsultationScheduleConflictError(Exception):
    pass


class ConsultationCopySourceNotFoundError(Exception):
    pass


@dataclass(slots=True)
class CreateConsultationInput:
    consultation_date: date | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    status: str | None = None
    diagnosis: str | None = None
    notes: str | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None
    medical_history_body: str | None = None
    continuous_medications: list[ConsultationMedicationInput] | None = None


@dataclass(slots=True)
class UpdateConsultationInput:
    fields: dict[str, object]


class ConsultationService:
    DEFAULT_SCHEDULE_DURATION = timedelta(minutes=30)
    ALLOWED_STATUSES = {
        CONSULTATION_STATUS_SCHEDULED,
        CONSULTATION_STATUS_COMPLETED,
        CONSULTATION_STATUS_CANCELLED,
    }

    def __init__(
        self,
        consultation_repository: ConsultationRepository,
        patient_repository: PatientRepository,
        medical_history_repository: MedicalHistoryRepository | None = None,
        continuous_medication_repository: ContinuousMedicationRepository | None = None,
        evolution_repository: EvolutionRepository | None = None,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.consultation_repository = consultation_repository
        self.patient_repository = patient_repository
        self.medical_history_repository = medical_history_repository
        self.continuous_medication_repository = continuous_medication_repository
        self.evolution_repository = evolution_repository
        self.audit_event_service = audit_event_service

    async def list_consultations(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Consultation]:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise ConsultationPatientNotFoundError("Patient not found")

        return await self.consultation_repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )

    async def list_consultations_by_interval(
        self,
        doctor_id: UUID,
        start_at: datetime,
        end_at: datetime,
        status: str | None,
    ) -> list[Consultation]:
        normalized_start_at = self._require_timezone_aware(start_at, "start_at")
        normalized_end_at = self._require_timezone_aware(end_at, "end_at")
        if normalized_end_at <= normalized_start_at:
            raise ConsultationValidationError("end_at must be greater than start_at")

        normalized_status = self._normalize_status(status) if status is not None else None
        return await self.consultation_repository.list_by_doctor_interval(
            doctor_id=doctor_id,
            start_at=normalized_start_at,
            end_at=normalized_end_at,
            status=normalized_status,
        )

    async def create_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateConsultationInput,
    ) -> Consultation:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise ConsultationPatientNotFoundError("Patient not found")
        latest_existing = await self.consultation_repository.get_latest_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )

        consultation = Consultation(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_date=payload.consultation_date,
            scheduled_start_at=payload.scheduled_start_at,
            scheduled_end_at=payload.scheduled_end_at,
            status=payload.status,
            diagnosis=payload.diagnosis,
            notes=payload.notes,
            chief_complaint=payload.chief_complaint,
            physical_exam=payload.physical_exam,
            conduct=payload.conduct,
        )
        consultation = await self._normalize_for_persistence(consultation=consultation, doctor_id=doctor_id)
        created = await self.consultation_repository.create(consultation=consultation)
        await self._copy_latest_snapshots(
            doctor_id=doctor_id,
            patient_id=patient_id,
            new_consultation_id=created.id,
            source_consultation=latest_existing,
        )
        if payload.medical_history_body is not None or payload.continuous_medications is not None:
            await self._sync_consultation_snapshots(
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=created.id,
                medical_history_body=payload.medical_history_body,
                continuous_medications=payload.continuous_medications,
            )
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="consultation",
                entity_id=created.id,
                action="create",
                event_type="ConsultationCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created

    async def get_consultation(self, doctor_id: UUID, consultation_id: UUID) -> Consultation:
        consultation = await self.consultation_repository.get_by_id(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
        )
        if consultation is None:
            raise ConsultationNotFoundError("Consultation not found")
        return consultation

    async def update_consultation(
        self,
        doctor_id: UUID,
        consultation_id: UUID,
        payload: UpdateConsultationInput,
    ) -> Consultation:
        existing = await self.get_consultation(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
        )
        updated = Consultation(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_date=self._resolve_field(payload.fields, "consultation_date", existing.consultation_date),
            scheduled_start_at=self._resolve_field(
                payload.fields, "scheduled_start_at", existing.scheduled_start_at
            ),
            scheduled_end_at=self._resolve_field(
                payload.fields, "scheduled_end_at", existing.scheduled_end_at
            ),
            status=self._resolve_field(payload.fields, "status", existing.status),
            diagnosis=self._resolve_field(payload.fields, "diagnosis", existing.diagnosis),
            notes=self._resolve_field(payload.fields, "notes", existing.notes),
            chief_complaint=self._resolve_field(payload.fields, "chief_complaint", existing.chief_complaint),
            physical_exam=self._resolve_field(payload.fields, "physical_exam", existing.physical_exam),
            conduct=self._resolve_field(payload.fields, "conduct", existing.conduct),
            created_at=existing.created_at,
        )
        updated = await self._normalize_for_persistence(
            consultation=updated,
            doctor_id=doctor_id,
            previous=existing,
            provided_fields=payload.fields,
        )
        saved = await self.consultation_repository.update(consultation=updated)
        if "medical_history_body" in payload.fields or "continuous_medications" in payload.fields:
            await self._sync_consultation_snapshots(
                doctor_id=doctor_id,
                patient_id=existing.patient_id,
                consultation_id=consultation_id,
                medical_history_body=payload.fields.get("medical_history_body"),
                continuous_medications=payload.fields.get("continuous_medications"),
            )
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="consultation",
                entity_id=saved.id,
                action="update",
                event_type="ConsultationUpdated",
                before_state=to_audit_dict(existing),
                after_state=to_audit_dict(saved),
            )
        return saved

    async def list_consultation_evolutions(
        self,
        doctor_id: UUID,
        consultation_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        if self.evolution_repository is None:
            raise RuntimeError("Evolution repository not configured")
        consultation = await self.get_consultation(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
        )
        return await self.evolution_repository.list_by_consultation(
            doctor_id=doctor_id,
            patient_id=consultation.patient_id,
            consultation_id=consultation_id,
            page=page,
            page_size=page_size,
        )

    async def copy_latest_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> Consultation:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise ConsultationPatientNotFoundError("Patient not found")

        latest = await self.consultation_repository.get_latest_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if latest is None:
            raise ConsultationCopySourceNotFoundError("No consultation available to copy")

        return await self.create_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateConsultationInput(
                consultation_date=date.today(),
                diagnosis=latest.diagnosis,
                notes=latest.notes,
                chief_complaint=latest.chief_complaint,
                physical_exam=latest.physical_exam,
                conduct=latest.conduct,
            ),
        )

    async def _copy_latest_snapshots(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        new_consultation_id: UUID,
        source_consultation: Consultation | None,
    ) -> None:
        if source_consultation is None or source_consultation.id == new_consultation_id:
            return

        if self.medical_history_repository is not None:
            latest_history = await self.medical_history_repository.get_latest_for_consultation(
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=source_consultation.id,
            )
            if latest_history is not None:
                await self.medical_history_repository.create(
                    MedicalHistory(
                        id=uuid4(),
                        doctor_id=doctor_id,
                        patient_id=patient_id,
                        consultation_id=new_consultation_id,
                        body=latest_history.body,
                    )
                )

        if self.continuous_medication_repository is not None:
            latest_medications = await self.continuous_medication_repository.list_by_consultation(
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=source_consultation.id,
            )
            for item in latest_medications:
                await self.continuous_medication_repository.create(
                    ContinuousMedication(
                        id=uuid4(),
                        doctor_id=doctor_id,
                        patient_id=patient_id,
                        consultation_id=new_consultation_id,
                        name=item.name,
                        dosage=item.dosage,
                        notes=item.notes,
                        status=item.status,
                    )
                )

    async def _sync_consultation_snapshots(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
        medical_history_body: str | None,
        continuous_medications: list[ConsultationMedicationInput] | None,
    ) -> None:
        if self.medical_history_repository is not None and medical_history_body is not None:
            normalized_body = medical_history_body.strip()
            current_histories = await self.medical_history_repository.list_by_patient(
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=consultation_id,
            )
            latest_history = current_histories[0] if current_histories else None
            if not normalized_body:
                for history in current_histories:
                    await self.medical_history_repository.delete(
                        doctor_id=doctor_id,
                        history_id=history.id,
                    )
            elif latest_history is None:
                await self.medical_history_repository.create(
                    MedicalHistory(
                        id=uuid4(),
                        doctor_id=doctor_id,
                        patient_id=patient_id,
                        consultation_id=consultation_id,
                        body=normalized_body,
                    )
                )
            else:
                await self.medical_history_repository.update(
                    MedicalHistory(
                        id=latest_history.id,
                        doctor_id=latest_history.doctor_id,
                        patient_id=latest_history.patient_id,
                        consultation_id=consultation_id,
                        body=normalized_body,
                        created_at=latest_history.created_at,
                        updated_at=latest_history.updated_at,
                    )
                )
                for history in current_histories[1:]:
                    await self.medical_history_repository.delete(
                        doctor_id=doctor_id,
                        history_id=history.id,
                    )

        if self.continuous_medication_repository is not None and continuous_medications is not None:
            current_medications = await self.continuous_medication_repository.list_by_consultation(
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=consultation_id,
            )
            existing_by_id = {item.id: item for item in current_medications}
            retained_ids: set[UUID] = set()
            for item in continuous_medications:
                normalized_name = item.name.strip()
                if not normalized_name:
                    raise ConsultationValidationError("Medication name is required")
                normalized_status = (
                    "active" if item.active else "inactive"
                )
                if item.id is not None and item.id in existing_by_id:
                    existing = existing_by_id[item.id]
                    retained_ids.add(existing.id)
                    await self.continuous_medication_repository.update(
                        ContinuousMedication(
                            id=existing.id,
                            doctor_id=existing.doctor_id,
                            patient_id=existing.patient_id,
                            consultation_id=consultation_id,
                            name=normalized_name,
                            dosage=item.dosage,
                            notes=item.notes,
                            status=normalized_status,
                            created_at=existing.created_at,
                        )
                    )
                else:
                    created = await self.continuous_medication_repository.create(
                        ContinuousMedication(
                            id=uuid4(),
                            doctor_id=doctor_id,
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            name=normalized_name,
                            dosage=item.dosage,
                            notes=item.notes,
                            status=normalized_status,
                        )
                    )
                    retained_ids.add(created.id)

            for existing in current_medications:
                if existing.id not in retained_ids:
                    await self.continuous_medication_repository.delete(
                        doctor_id=doctor_id,
                        medication_id=existing.id,
                    )

    async def _normalize_for_persistence(
        self,
        consultation: Consultation,
        doctor_id: UUID,
        previous: Consultation | None = None,
        provided_fields: dict[str, object] | None = None,
    ) -> Consultation:
        scheduled_start_at = consultation.scheduled_start_at
        scheduled_end_at = consultation.scheduled_end_at

        if scheduled_start_at is not None:
            scheduled_start_at = self._require_timezone_aware(
                scheduled_start_at, "scheduled_start_at"
            )
        if scheduled_end_at is not None:
            scheduled_end_at = self._require_timezone_aware(scheduled_end_at, "scheduled_end_at")

        should_default_end = scheduled_start_at is not None and (
            (previous is None and scheduled_end_at is None)
            or (
                previous is not None
                and provided_fields is not None
                and "scheduled_start_at" in provided_fields
                and "scheduled_end_at" not in provided_fields
            )
        )
        if should_default_end:
            scheduled_end_at = scheduled_start_at + self.DEFAULT_SCHEDULE_DURATION

        if (scheduled_start_at is None) != (scheduled_end_at is None):
            raise ConsultationValidationError(
                "scheduled_start_at and scheduled_end_at must be provided together"
            )

        if scheduled_start_at is not None and scheduled_end_at <= scheduled_start_at:
            raise ConsultationValidationError("scheduled_end_at must be greater than scheduled_start_at")

        status = self._normalize_status(consultation.status)
        if status is None:
            status = CONSULTATION_STATUS_SCHEDULED

        consultation_date = consultation.consultation_date
        if scheduled_start_at is not None:
            consultation_date = scheduled_start_at.date()

        normalized = Consultation(
            id=consultation.id,
            doctor_id=consultation.doctor_id,
            patient_id=consultation.patient_id,
            consultation_date=consultation_date,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            status=status,
            diagnosis=consultation.diagnosis,
            notes=consultation.notes,
            chief_complaint=consultation.chief_complaint,
            physical_exam=consultation.physical_exam,
            conduct=consultation.conduct,
            created_at=consultation.created_at,
        )

        if (
            normalized.scheduled_start_at is not None
            and normalized.scheduled_end_at is not None
            and normalized.status != CONSULTATION_STATUS_CANCELLED
        ):
            has_overlap = await self.consultation_repository.has_schedule_overlap(
                doctor_id=doctor_id,
                scheduled_start_at=normalized.scheduled_start_at,
                scheduled_end_at=normalized.scheduled_end_at,
                exclude_consultation_id=normalized.id if previous is not None else None,
            )
            if has_overlap:
                raise ConsultationScheduleConflictError("Consultation schedule overlaps an existing consultation")

        return normalized

    @classmethod
    def _normalize_status(cls, status: str | None) -> str | None:
        if status is None:
            return None
        normalized = status.strip()
        if normalized not in cls.ALLOWED_STATUSES:
            raise ConsultationValidationError("Invalid status")
        return normalized

    @staticmethod
    def _require_timezone_aware(value: datetime, field_name: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ConsultationValidationError(f"{field_name} must include timezone")
        return value

    @staticmethod
    def _resolve_field(fields: dict[str, object], field_name: str, current_value: object) -> object:
        if field_name in fields:
            return fields[field_name]
        return current_value
