from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.consultation import Consultation


class ConsultationPatientNotFoundError(Exception):
    pass


@dataclass(slots=True)
class CreateConsultationInput:
    consultation_date: date | None = None
    chief_complaint: str | None = None
    physical_exam: str | None = None
    conduct: str | None = None


class ConsultationService:
    def __init__(
        self,
        consultation_repository: ConsultationRepository,
        patient_repository: PatientRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.consultation_repository = consultation_repository
        self.patient_repository = patient_repository
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

        consultation = Consultation(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_date=payload.consultation_date,
            chief_complaint=payload.chief_complaint,
            physical_exam=payload.physical_exam,
            conduct=payload.conduct,
        )
        created = await self.consultation_repository.create(consultation=consultation)
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
