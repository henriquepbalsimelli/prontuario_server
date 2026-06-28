from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.medication_repository import MedicationRepository
from app.domain.models.medication import Medication
from app.infrastructure.database.models import Medication as MedicationModel


class SQLAlchemyMedicationRepository(MedicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: MedicationModel) -> Medication:
        return Medication(
            id=model.id,
            name=model.name,
            active_principle=model.active_principle,
            form=model.form,
            notes=model.notes,
        )

    async def list_all(self, page: int, page_size: int) -> list[Medication]:
        offset = (page - 1) * page_size
        stmt = (
            select(MedicationModel)
            .order_by(MedicationModel.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def create(self, medication: Medication) -> Medication:
        row = MedicationModel(
            id=medication.id,
            name=medication.name,
            active_principle=medication.active_principle,
            form=medication.form,
            notes=medication.notes,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)
