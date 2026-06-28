from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.interfaces.doctor_template_repository import DoctorTemplateRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.interfaces.text_document_repository import TextDocumentRepository
from app.domain.models.text_document import TextDocument


class TextDocumentPatientNotFoundError(Exception):
    pass


class TextDocumentNotFoundError(Exception):
    pass


class TextDocumentValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateTextDocumentFromTemplateInput:
    template_id: UUID
    title: str | None = None
    body: str | None = None
    consultation_id: UUID | None = None


@dataclass(slots=True)
class UpdateTextDocumentInput:
    type: str
    title: str
    body: str
    consultation_id: UUID | None = None


class TextDocumentService:
    def __init__(
        self,
        repository: TextDocumentRepository,
        patient_repository: PatientRepository,
        consultation_repository: ConsultationRepository,
        template_repository: DoctorTemplateRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.patient_repository = patient_repository
        self.consultation_repository = consultation_repository
        self.template_repository = template_repository
        self.audit_event_service = audit_event_service

    async def list_documents(self, doctor_id: UUID, patient_id: UUID) -> list[TextDocument]:
        await self._require_patient(doctor_id, patient_id)
        return await self.repository.list_by_patient(doctor_id=doctor_id, patient_id=patient_id)

    async def get_document(self, doctor_id: UUID, document_id: UUID) -> TextDocument:
        document = await self.repository.get_by_id(doctor_id=doctor_id, document_id=document_id)
        if document is None:
            raise TextDocumentNotFoundError("Text document not found")
        return document

    async def create_from_template(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        payload: CreateTextDocumentFromTemplateInput,
    ) -> TextDocument:
        await self._require_patient(doctor_id, patient_id)
        await self._validate_consultation_reference(doctor_id, patient_id, payload.consultation_id)
        template = await self.template_repository.get_by_id(doctor_id=doctor_id, template_id=payload.template_id)
        if template is None:
            raise TextDocumentValidationError("Template not found")
        document = TextDocument(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=payload.consultation_id,
            template_id=template.id,
            type=template.type,
            title=(payload.title or template.title).strip(),
            body=(payload.body or template.body).strip(),
            version=1,
        )
        if not document.title or not document.body:
            raise TextDocumentValidationError("Title and body are required")
        created = await self.repository.create(document)
        await self._audit("create", "TextDocumentCreated", doctor_id, created.id, None, created)
        return created

    async def update_document(self, doctor_id: UUID, document_id: UUID, payload: UpdateTextDocumentInput) -> TextDocument:
        existing = await self.get_document(doctor_id, document_id)
        await self._validate_consultation_reference(doctor_id, existing.patient_id, payload.consultation_id)
        updated = TextDocument(
            id=existing.id,
            doctor_id=existing.doctor_id,
            patient_id=existing.patient_id,
            consultation_id=payload.consultation_id,
            template_id=existing.template_id,
            type=payload.type.strip(),
            title=payload.title.strip(),
            body=payload.body.strip(),
            version=existing.version + 1,
            created_at=existing.created_at,
        )
        if not updated.type or not updated.title or not updated.body:
            raise TextDocumentValidationError("Type, title and body are required")
        saved = await self.repository.update(updated)
        await self._audit("update", "TextDocumentUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_document(self, doctor_id: UUID, document_id: UUID) -> None:
        existing = await self.get_document(doctor_id, document_id)
        deleted = await self.repository.delete(doctor_id=doctor_id, document_id=document_id)
        if not deleted:
            raise TextDocumentNotFoundError("Text document not found")
        await self._audit("delete", "TextDocumentDeleted", doctor_id, document_id, existing, None)

    async def _require_patient(self, doctor_id: UUID, patient_id: UUID) -> None:
        patient = await self.patient_repository.get_by_id(doctor_id=doctor_id, patient_id=patient_id)
        if patient is None:
            raise TextDocumentPatientNotFoundError("Patient not found")

    async def _validate_consultation_reference(self, doctor_id: UUID, patient_id: UUID, consultation_id: UUID | None) -> None:
        if consultation_id is None:
            return
        consultation = await self.consultation_repository.get_by_id(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            patient_id=patient_id,
        )
        if consultation is None:
            raise TextDocumentValidationError("Consultation not found for patient")

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="text_document",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
