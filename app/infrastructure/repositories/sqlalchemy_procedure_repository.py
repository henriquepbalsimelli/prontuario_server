from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.procedure_repository import ProcedureRepository
from app.domain.models.procedure import Procedure
from app.infrastructure.database.models import Procedure as ProcedureModel


class SQLAlchemyProcedureRepository(ProcedureRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ProcedureModel) -> Procedure:
        return Procedure(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            procedure_date=model.procedure_date,
            title=model.title,
            description=model.description,
            notes=model.notes,
            created_at=model.created_at,
        )

    async def list_by_patient(self, doctor_id: UUID, patient_id: UUID) -> list[Procedure]:
        stmt = (
            select(ProcedureModel)
            .where(
                ProcedureModel.doctor_id == doctor_id,
                ProcedureModel.patient_id == patient_id,
            )
            .order_by(ProcedureModel.procedure_date.desc(), ProcedureModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_by_id(self, doctor_id: UUID, procedure_id: UUID) -> Procedure | None:
        stmt = select(ProcedureModel).where(
            ProcedureModel.id == procedure_id,
            ProcedureModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, procedure: Procedure) -> Procedure:
        row = ProcedureModel(
            id=procedure.id,
            doctor_id=procedure.doctor_id,
            patient_id=procedure.patient_id,
            consultation_id=procedure.consultation_id,
            procedure_date=procedure.procedure_date,
            title=procedure.title,
            description=procedure.description,
            notes=procedure.notes,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, procedure: Procedure) -> Procedure:
        stmt = select(ProcedureModel).where(
            ProcedureModel.id == procedure.id,
            ProcedureModel.doctor_id == procedure.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.consultation_id = procedure.consultation_id
        row.procedure_date = procedure.procedure_date
        row.title = procedure.title
        row.description = procedure.description
        row.notes = procedure.notes
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, procedure_id: UUID) -> bool:
        stmt = delete(ProcedureModel).where(
            ProcedureModel.id == procedure_id,
            ProcedureModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
