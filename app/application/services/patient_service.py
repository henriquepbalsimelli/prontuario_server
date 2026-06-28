from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.patient import Patient


class PatientNotFoundError(Exception):
    pass


@dataclass(slots=True)
class CreatePatientInput:
    name: str
    birth_date: date | None = None
    gender: str | None = None
    phone: str | None = None
    medical_history: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class UpdatePatientInput:
    name: str
    birth_date: date | None = None
    gender: str | None = None
    phone: str | None = None
    medical_history: str | None = None
    notes: str | None = None


class PatientService:
    def __init__(
        self,
        repository: PatientRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_event_service = audit_event_service

    async def list_patients(
        self,
        doctor_id: UUID,
        page: int,
        page_size: int,
        name: str | None = None,
    ) -> list[Patient]:
        normalized_name = name.strip() if name is not None else None
        if normalized_name == "":
            normalized_name = None

        return await self.repository.list_by_doctor(
            doctor_id=doctor_id,
            page=page,
            page_size=page_size,
            name=normalized_name,
        )

    async def get_patient(self, doctor_id: UUID, patient_id: UUID) -> Patient:
        patient = await self.repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise PatientNotFoundError("Patient not found")
        return patient

    async def create_patient(self, doctor_id: UUID, payload: CreatePatientInput) -> Patient:
        patient = Patient(
            id=uuid4(),
            doctor_id=doctor_id,
            name=payload.name,
            birth_date=payload.birth_date,
            gender=payload.gender,
            phone=payload.phone,
            medical_history=payload.medical_history,
            notes=payload.notes,
        )
        created = await self.repository.create(patient=patient)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="patient",
                entity_id=created.id,
                action="create",
                event_type="PatientCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created

    async def update_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: UpdatePatientInput,
    ) -> Patient:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if existing is None:
            raise PatientNotFoundError("Patient not found")

        updated = Patient(
            id=existing.id,
            doctor_id=existing.doctor_id,
            name=payload.name,
            birth_date=payload.birth_date,
            gender=payload.gender,
            phone=payload.phone,
            medical_history=payload.medical_history,
            notes=payload.notes,
            created_at=existing.created_at,
        )
        saved = await self.repository.update(patient=updated)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="patient",
                entity_id=saved.id,
                action="update",
                event_type="PatientUpdated",
                before_state=to_audit_dict(existing),
                after_state=to_audit_dict(saved),
            )
        return saved

    async def delete_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        existing = await self.repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if existing is None:
            raise PatientNotFoundError("Patient not found")
        deleted = await self.repository.delete(doctor_id=doctor_id, patient_id=patient_id)
        if not deleted:
            raise PatientNotFoundError("Patient not found")
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="patient",
                entity_id=patient_id,
                action="delete",
                event_type="PatientDeleted",
                before_state=to_audit_dict(existing),
                after_state=None,
            )
