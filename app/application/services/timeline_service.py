from uuid import UUID

from app.application.services.consultation_service import ConsultationPatientNotFoundError
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.interfaces.procedure_repository import ProcedureRepository
from app.domain.models.timeline import (
    TIMELINE_SOURCE_CONSULTATION,
    TIMELINE_SOURCE_PROCEDURE,
    TimelineEvent,
)


class TimelineService:
    ALLOWED_TYPES = {TIMELINE_SOURCE_CONSULTATION, TIMELINE_SOURCE_PROCEDURE}

    def __init__(
        self,
        consultation_repository: ConsultationRepository,
        procedure_repository: ProcedureRepository,
        patient_repository: PatientRepository,
    ) -> None:
        self.consultation_repository = consultation_repository
        self.procedure_repository = procedure_repository
        self.patient_repository = patient_repository

    async def list_timeline(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        types: list[str] | None,
    ) -> list[TimelineEvent]:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise ConsultationPatientNotFoundError("Patient not found")

        normalized_types = self._normalize_types(types)
        events: list[TimelineEvent] = []

        if TIMELINE_SOURCE_CONSULTATION in normalized_types:
            consultations = await self.consultation_repository.list_by_patient(
                doctor_id=doctor_id,
                patient_id=patient_id,
                page=1,
                page_size=200,
            )
            events.extend(
                TimelineEvent(
                    id=f"consultation:{item.id}",
                    source_type=TIMELINE_SOURCE_CONSULTATION,
                    occurred_at=item.consultation_date,
                    title="Evolucao clinica/consulta",
                    summary=item.diagnosis or item.chief_complaint or item.conduct,
                    consultation_id=item.id,
                    source_id=item.id,
                )
                for item in consultations
            )

        if TIMELINE_SOURCE_PROCEDURE in normalized_types:
            procedures = await self.procedure_repository.list_by_patient(
                doctor_id=doctor_id,
                patient_id=patient_id,
            )
            events.extend(
                TimelineEvent(
                    id=f"procedure:{item.id}",
                    source_type=TIMELINE_SOURCE_PROCEDURE,
                    occurred_at=item.procedure_date,
                    title=item.title,
                    summary=item.description or item.notes,
                    consultation_id=item.consultation_id,
                    source_id=item.id,
                )
                for item in procedures
            )

        events.sort(
            key=lambda item: (
                item.occurred_at is None,
                item.occurred_at,
                item.id,
            ),
            reverse=True,
        )
        return events

    def _normalize_types(self, types: list[str] | None) -> set[str]:
        if not types:
            return set(self.ALLOWED_TYPES)
        normalized = {item.strip().lower() for item in types if item and item.strip()}
        invalid = normalized - self.ALLOWED_TYPES
        if invalid:
            raise ValueError("Invalid timeline type")
        return normalized
