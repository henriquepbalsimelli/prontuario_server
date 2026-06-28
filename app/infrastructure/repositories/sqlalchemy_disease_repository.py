from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.disease_repository import DiseaseRepository
from app.domain.models.disease import Disease
from app.infrastructure.database.models import Disease as DiseaseModel


class SQLAlchemyDiseaseRepository(DiseaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: DiseaseModel) -> Disease:
        return Disease(
            id=model.id,
            name=model.name,
            cid10=model.cid10,
            description=model.description,
        )

    async def list_all(self, page: int, page_size: int) -> list[Disease]:
        offset = (page - 1) * page_size
        stmt = (
            select(DiseaseModel)
            .order_by(DiseaseModel.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def create(self, disease: Disease) -> Disease:
        row = DiseaseModel(
            id=disease.id,
            name=disease.name,
            cid10=disease.cid10,
            description=disease.description,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)
