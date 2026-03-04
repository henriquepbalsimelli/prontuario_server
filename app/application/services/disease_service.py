from dataclasses import dataclass
from uuid import UUID
from uuid import uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.disease_repository import DiseaseRepository
from app.domain.models.disease import Disease


@dataclass(slots=True)
class CreateDiseaseInput:
    name: str
    cid10: str | None = None
    description: str | None = None


class DiseaseService:
    def __init__(
        self,
        repository: DiseaseRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_event_service = audit_event_service

    async def list_diseases(self, page: int, page_size: int) -> list[Disease]:
        return await self.repository.list_all(page=page, page_size=page_size)

    async def create_disease(
        self,
        actor_doctor_id: UUID,
        payload: CreateDiseaseInput,
    ) -> Disease:
        disease = Disease(
            id=uuid4(),
            name=payload.name.strip(),
            cid10=payload.cid10,
            description=payload.description,
        )
        created = await self.repository.create(disease=disease)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=actor_doctor_id,
                entity_type="disease",
                entity_id=created.id,
                action="create",
                event_type="DiseaseCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created
