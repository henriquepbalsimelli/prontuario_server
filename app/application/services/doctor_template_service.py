from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.doctor_template_repository import DoctorTemplateRepository
from app.domain.models.doctor_template import (
    DOCTOR_TEMPLATE_TYPE_CONDUCT,
    DOCTOR_TEMPLATE_TYPE_GENERAL,
    DOCTOR_TEMPLATE_TYPE_PRESCRIPTION,
    DoctorTemplate,
)


class DoctorTemplateNotFoundError(Exception):
    pass


class DoctorTemplateValidationError(Exception):
    pass


@dataclass(slots=True)
class CreateDoctorTemplateInput:
    title: str
    type: str
    body: str


@dataclass(slots=True)
class UpdateDoctorTemplateInput:
    title: str
    type: str
    body: str


class DoctorTemplateService:
    ALLOWED_TYPES = {
        DOCTOR_TEMPLATE_TYPE_CONDUCT,
        DOCTOR_TEMPLATE_TYPE_PRESCRIPTION,
        DOCTOR_TEMPLATE_TYPE_GENERAL,
    }

    def __init__(
        self,
        repository: DoctorTemplateRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_event_service = audit_event_service

    async def list_templates(self, doctor_id: UUID, template_type: str | None = None) -> list[DoctorTemplate]:
        normalized_type = self._normalize_type(template_type) if template_type is not None else None
        return await self.repository.list_by_doctor(doctor_id=doctor_id, template_type=normalized_type)

    async def get_template(self, doctor_id: UUID, template_id: UUID) -> DoctorTemplate:
        template = await self.repository.get_by_id(doctor_id=doctor_id, template_id=template_id)
        if template is None:
            raise DoctorTemplateNotFoundError("Template not found")
        return template

    async def create_template(self, doctor_id: UUID, payload: CreateDoctorTemplateInput) -> DoctorTemplate:
        template = DoctorTemplate(
            id=uuid4(),
            doctor_id=doctor_id,
            title=self._require_text(payload.title, "Title"),
            type=self._normalize_type(payload.type),
            body=self._require_text(payload.body, "Body"),
        )
        created = await self.repository.create(template)
        await self._audit("create", "DoctorTemplateCreated", doctor_id, created.id, None, created)
        return created

    async def update_template(self, doctor_id: UUID, template_id: UUID, payload: UpdateDoctorTemplateInput) -> DoctorTemplate:
        existing = await self.get_template(doctor_id, template_id)
        updated = DoctorTemplate(
            id=existing.id,
            doctor_id=existing.doctor_id,
            title=self._require_text(payload.title, "Title"),
            type=self._normalize_type(payload.type),
            body=self._require_text(payload.body, "Body"),
            created_at=existing.created_at,
        )
        saved = await self.repository.update(updated)
        await self._audit("update", "DoctorTemplateUpdated", doctor_id, saved.id, existing, saved)
        return saved

    async def delete_template(self, doctor_id: UUID, template_id: UUID) -> None:
        existing = await self.get_template(doctor_id, template_id)
        deleted = await self.repository.delete(doctor_id=doctor_id, template_id=template_id)
        if not deleted:
            raise DoctorTemplateNotFoundError("Template not found")
        await self._audit("delete", "DoctorTemplateDeleted", doctor_id, template_id, existing, None)

    def _normalize_type(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in self.ALLOWED_TYPES:
            raise DoctorTemplateValidationError("Invalid template type")
        return normalized

    def _require_text(self, value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise DoctorTemplateValidationError(f"{field_name} is required")
        return normalized

    async def _audit(self, action: str, event_type: str, doctor_id: UUID, entity_id: UUID, before, after) -> None:
        if self.audit_event_service is None:
            return
        await self.audit_event_service.record_write(
            doctor_id=doctor_id,
            entity_type="doctor_template",
            entity_id=entity_id,
            action=action,
            event_type=event_type,
            before_state=to_audit_dict(before),
            after_state=to_audit_dict(after),
        )
