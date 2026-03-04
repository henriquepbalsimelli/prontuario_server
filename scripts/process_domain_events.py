from __future__ import annotations

import argparse
import asyncio

from app.application.services.domain_event_processor_service import DomainEventProcessorService
from app.infrastructure.event_bus import SQLAlchemyDomainEventBus
from app.presentation.main import app


async def _run(limit: int) -> None:
    container = app.state.container
    async for session in container.db_session():
        bus = SQLAlchemyDomainEventBus(session=session)
        service = DomainEventProcessorService(event_bus=bus)
        processed = await service.process_pending(limit=limit)
        print(f"processed_events={processed}")
        break


def main() -> None:
    parser = argparse.ArgumentParser(description="Process pending domain events")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(_run(limit=args.limit))


if __name__ == "__main__":
    main()
