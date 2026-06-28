from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.evolution_repository import EvolutionRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.evolution import Evolution

ALLOWED_EVOLUTION_ORIGIN_TYPES = {
    "consultation",
    "inpatient_visit",
    "exam_review",
    "phone_contact",
    "telemedicine",
    "procedure",
    "hospital_event",
    "multidisciplinary_discussion",
    "other",
}


class EvolutionNotFoundError(Exception):
    pass


class EvolutionPatientNotFoundError(Exception):
    pass


class EvolutionConsultationNotFoundError(Exception):
    pass


class EvolutionValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateEvolutionInput:
    consultation_id: UUID | None
    origin_type: str
    content: str
    occurred_at: datetime


@dataclass(slots=True)
class UpdateEvolutionInput:
    consultation_id: UUID | None
    origin_type: str
    content: str
    occurred_at: datetime


class EvolutionService:
    def __init__(
        self,
        repository: EvolutionRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.audit_event_service = audit_event_service

    async def list_evolutions(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        await self._ensure_patient_exists(doctor_id=doctor_id, patient_id=patient_id)
        return await self.repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )

    async def get_evolution(self, doctor_id: UUID, evolution_id: UUID) -> Evolution:
        evolution = await self.repository.get_by_id(
            doctor_id=doctor_id,
            evolution_id=evolution_id,
        )
        if evolution is None:
            raise EvolutionNotFoundError("Evolution not found")
        return evolution

    async def create_evolution(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateEvolutionInput,
    ) -> Evolution:
        await self._ensure_patient_exists(doctor_id=doctor_id, patient_id=patient_id)
        normalized_content = self._normalize_content(payload.content)
        normalized_origin_type = self._normalize_origin_type(payload.origin_type)
        await self._validate_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
        )

        evolution = Evolution(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
            origin_type=normalized_origin_type,
            content=normalized_content,
            occurred_at=payload.occurred_at,
        )
        created = await self.repository.create(evolution=evolution)

        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="evolution",
                entity_id=created.id,
                action="create",
                event_type="EvolutionCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )

        return created

    async def update_evolution(
        self,
        doctor_id: UUID,
        evolution_id: UUID,
        payload: UpdateEvolutionInput,
    ) -> Evolution:
        existing = await self.get_evolution(doctor_id=doctor_id, evolution_id=evolution_id)
        normalized_content = self._normalize_content(payload.content)
        normalized_origin_type = self._normalize_origin_type(payload.origin_type)
        await self._validate_consultation(
            doctor_id=doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
        )

        updated = Evolution(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
            origin_type=normalized_origin_type,
            content=normalized_content,
            occurred_at=payload.occurred_at,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = await self.repository.update(evolution=updated)

        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="evolution",
                entity_id=saved.id,
                action="update",
                event_type="EvolutionUpdated",
                before_state=to_audit_dict(existing),
                after_state=to_audit_dict(saved),
            )

        return saved

    async def _ensure_patient_exists(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise EvolutionPatientNotFoundError("Patient not found")

    async def _validate_consultation(
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
            raise EvolutionConsultationNotFoundError("Consultation not found")

    @staticmethod
    def _normalize_content(content: str) -> str:
        normalized = content.strip()
        if not normalized:
            raise EvolutionValidationError("Content must not be empty")
        return normalized

    @staticmethod
    def _normalize_origin_type(origin_type: str) -> str:
        normalized = origin_type.strip()
        if normalized not in ALLOWED_EVOLUTION_ORIGIN_TYPES:
            raise EvolutionValidationError("Invalid origin_type")
        return normalized
