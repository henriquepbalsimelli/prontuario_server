from __future__ import annotations

from app.application.event_bus.contracts import DomainEventBus


class DomainEventProcessorService:
    def __init__(self, event_bus: DomainEventBus) -> None:
        self.event_bus = event_bus

    async def process_pending(self, limit: int = 100) -> int:
        return await self.event_bus.process_pending(limit=limit)
