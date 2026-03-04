from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.services.health_service import HealthService
from app.infrastructure.database.session import create_engine, create_session_factory
from app.infrastructure.settings import Settings


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = create_engine(settings=settings)
        self.session_factory: async_sessionmaker[AsyncSession] = create_session_factory(
            engine=self.engine
        )

    def health_service(self) -> HealthService:
        return HealthService(
            app_name=self.settings.app_name,
            environment=self.settings.environment,
        )

    async def db_session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()
