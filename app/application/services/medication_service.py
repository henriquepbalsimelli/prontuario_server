from dataclasses import dataclass
from uuid import UUID
from uuid import uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.medication_repository import MedicationRepository
from app.domain.models.medication import Medication


@dataclass(slots=True)
class CreateMedicationInput:
    name: str
    active_principle: str | None = None
    form: str | None = None
    notes: str | None = None


class MedicationService:
    def __init__(
        self,
        repository: MedicationRepository,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_event_service = audit_event_service

    async def list_medications(self, page: int, page_size: int) -> list[Medication]:
        return await self.repository.list_all(page=page, page_size=page_size)

    async def create_medication(
        self,
        actor_doctor_id: UUID,
        payload: CreateMedicationInput,
    ) -> Medication:
        medication = Medication(
            id=uuid4(),
            name=payload.name.strip(),
            active_principle=payload.active_principle,
            form=payload.form,
            notes=payload.notes,
        )
        created = await self.repository.create(medication=medication)
        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=actor_doctor_id,
                entity_type="medication",
                entity_id=created.id,
                action="create",
                event_type="MedicationCreated",
                before_state=None,
                after_state=to_audit_dict(created),
            )
        return created
