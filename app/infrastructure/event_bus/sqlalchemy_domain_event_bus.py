from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.event_bus.contracts import DomainEventBus, PublishedDomainEvent
from app.infrastructure.database.models import DomainEvent

logger = structlog.get_logger(__name__)


class SQLAlchemyDomainEventBus(DomainEventBus):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_published_event(model: DomainEvent) -> PublishedDomainEvent:
        return PublishedDomainEvent(
            id=model.id,
            event_type=model.event_type,
            entity_id=model.entity_id,
            payload=model.payload,
            created_at=model.created_at,
            processed=model.processed,
            processed_at=model.processed_at,
        )

    async def publish(
        self,
        event_type: str,
        entity_id: UUID,
        payload: dict,
    ) -> PublishedDomainEvent:
        event = DomainEvent(
            event_type=event_type,
            entity_id=entity_id,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return self._to_published_event(event)

    async def process_pending(self, limit: int = 100) -> int:
        if limit <= 0:
            return 0

        stmt = (
            select(DomainEvent)
            .where(DomainEvent.processed.is_(False))
            .order_by(DomainEvent.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        events = list(result.scalars().all())

        processed_count = 0
        for event in events:
            # Placeholder handler hook. For now, just log and mark as processed.
            logger.info(
                "domain_event_processed",
                event_id=str(event.id),
                event_type=event.event_type,
                entity_id=str(event.entity_id),
            )
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            processed_count += 1

        if processed_count:
            await self.session.commit()

        return processed_count
