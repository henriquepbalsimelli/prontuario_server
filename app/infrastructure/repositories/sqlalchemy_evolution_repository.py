from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.evolution_repository import EvolutionRepository
from app.domain.models.evolution import Evolution
from app.infrastructure.database.models import Evolution as EvolutionModel


class SQLAlchemyEvolutionRepository(EvolutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: EvolutionModel) -> Evolution:
        return Evolution(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            origin_type=model.origin_type,
            content=model.content,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        offset = (page - 1) * page_size
        stmt = (
            select(EvolutionModel)
            .where(
                EvolutionModel.doctor_id == doctor_id,
                EvolutionModel.patient_id == patient_id,
            )
            .order_by(EvolutionModel.occurred_at.desc(), EvolutionModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, doctor_id: UUID, evolution_id: UUID) -> Evolution | None:
        stmt = select(EvolutionModel).where(
            EvolutionModel.id == evolution_id,
            EvolutionModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        offset = (page - 1) * page_size
        stmt = (
            select(EvolutionModel)
            .where(
                EvolutionModel.doctor_id == doctor_id,
                EvolutionModel.patient_id == patient_id,
                EvolutionModel.consultation_id == consultation_id,
            )
            .order_by(EvolutionModel.occurred_at.desc(), EvolutionModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def create(self, evolution: Evolution) -> Evolution:
        row = EvolutionModel(
            id=evolution.id,
            doctor_id=evolution.doctor_id,
            patient_id=evolution.patient_id,
            consultation_id=evolution.consultation_id,
            origin_type=evolution.origin_type,
            content=evolution.content,
            occurred_at=evolution.occurred_at,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, evolution: Evolution) -> Evolution:
        stmt = select(EvolutionModel).where(
            EvolutionModel.id == evolution.id,
            EvolutionModel.doctor_id == evolution.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()

        row.consultation_id = evolution.consultation_id
        row.origin_type = evolution.origin_type
        row.content = evolution.content
        row.occurred_at = evolution.occurred_at
        row.updated_at = func.now()

        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)
