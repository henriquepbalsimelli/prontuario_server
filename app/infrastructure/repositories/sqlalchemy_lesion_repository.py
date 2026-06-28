from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.lesion_repository import LesionRepository
from app.domain.models.lesion import Lesion
from app.infrastructure.database.models import Lesion as LesionModel


class SQLAlchemyLesionRepository(LesionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: LesionModel) -> Lesion:
        return Lesion(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            label=model.label,
            body_region=model.body_region,
            coord_x=model.coord_x,
            coord_y=model.coord_y,
            status=model.status,
            notes=model.notes,
            created_at=model.created_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Lesion]:
        offset = (page - 1) * page_size
        stmt = (
            select(LesionModel)
            .where(LesionModel.doctor_id == doctor_id, LesionModel.patient_id == patient_id)
            .order_by(LesionModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, doctor_id: UUID, lesion_id: UUID) -> Lesion | None:
        stmt = select(LesionModel).where(
            LesionModel.id == lesion_id,
            LesionModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def create(self, lesion: Lesion) -> Lesion:
        row = LesionModel(
            id=lesion.id,
            doctor_id=lesion.doctor_id,
            patient_id=lesion.patient_id,
            label=lesion.label,
            body_region=lesion.body_region,
            coord_x=lesion.coord_x,
            coord_y=lesion.coord_y,
            status=lesion.status,
            notes=lesion.notes,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, lesion: Lesion) -> Lesion:
        stmt = select(LesionModel).where(
            LesionModel.id == lesion.id,
            LesionModel.doctor_id == lesion.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()

        row.label = lesion.label
        row.body_region = lesion.body_region
        row.coord_x = lesion.coord_x
        row.coord_y = lesion.coord_y
        row.status = lesion.status
        row.notes = lesion.notes

        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)
