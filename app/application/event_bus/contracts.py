from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class PublishedDomainEvent:
    id: UUID
    event_type: str
    entity_id: UUID
    payload: dict
    created_at: datetime | None
    processed: bool
    processed_at: datetime | None


class DomainEventBus(ABC):
    @abstractmethod
    async def publish(
        self,
        event_type: str,
        entity_id: UUID,
        payload: dict,
    ) -> PublishedDomainEvent:
        raise NotImplementedError

    @abstractmethod
    async def process_pending(self, limit: int = 100) -> int:
        raise NotImplementedError
