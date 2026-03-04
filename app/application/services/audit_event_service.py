from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.event_bus.contracts import DomainEventBus
from app.infrastructure.database.models import AuditLog
from app.presentation.request_context import get_request_context


class AuditEventService:
    def __init__(self, session: AsyncSession, event_bus: DomainEventBus) -> None:
        self.session = session
        self.event_bus = event_bus

    async def record_write(
        self,
        doctor_id: UUID,
        entity_type: str,
        entity_id: UUID,
        action: str,
        event_type: str,
        before_state: dict | None,
        after_state: dict | None,
    ) -> None:
        ctx = get_request_context()

        audit = AuditLog(
            doctor_id=doctor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            request_id=ctx.request_id,
        )
        self.session.add(audit)

        event_payload = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
            "doctor_id": str(doctor_id),
            "request_id": ctx.request_id,
            "before_state": before_state,
            "after_state": after_state,
        }
        await self.event_bus.publish(
            event_type=event_type,
            entity_id=entity_id,
            payload=event_payload,
        )

        await self.session.commit()
