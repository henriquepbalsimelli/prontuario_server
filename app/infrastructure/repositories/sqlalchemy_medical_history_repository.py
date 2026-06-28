from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.medical_history_repository import MedicalHistoryRepository
from app.domain.models.medical_history import MedicalHistory
from app.infrastructure.database.models import PatientMedicalHistory as MedicalHistoryModel


class SQLAlchemyMedicalHistoryRepository(MedicalHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: MedicalHistoryModel) -> MedicalHistory:
        return MedicalHistory(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            body=model.body,
            created_at=model.created_at,
            updated_at=getattr(model, "updated_at", None),
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID | None = None,
    ) -> list[MedicalHistory]:
        stmt = select(MedicalHistoryModel).where(
            MedicalHistoryModel.doctor_id == doctor_id,
            MedicalHistoryModel.patient_id == patient_id,
        )
        if consultation_id is not None:
            stmt = stmt.where(MedicalHistoryModel.consultation_id == consultation_id)
        stmt = stmt.order_by(MedicalHistoryModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_by_id(self, doctor_id: UUID, history_id: UUID) -> MedicalHistory | None:
        stmt = select(MedicalHistoryModel).where(
            MedicalHistoryModel.id == history_id,
            MedicalHistoryModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def get_latest_for_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> MedicalHistory | None:
        stmt = (
            select(MedicalHistoryModel)
            .where(
                MedicalHistoryModel.doctor_id == doctor_id,
                MedicalHistoryModel.patient_id == patient_id,
            )
            .order_by(MedicalHistoryModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def get_latest_for_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
    ) -> MedicalHistory | None:
        stmt = (
            select(MedicalHistoryModel)
            .where(
                MedicalHistoryModel.doctor_id == doctor_id,
                MedicalHistoryModel.patient_id == patient_id,
                MedicalHistoryModel.consultation_id == consultation_id,
            )
            .order_by(MedicalHistoryModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, history: MedicalHistory) -> MedicalHistory:
        row = MedicalHistoryModel(
            id=history.id,
            doctor_id=history.doctor_id,
            patient_id=history.patient_id,
            consultation_id=history.consultation_id,
            body=history.body,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, history: MedicalHistory) -> MedicalHistory:
        stmt = select(MedicalHistoryModel).where(
            MedicalHistoryModel.id == history.id,
            MedicalHistoryModel.doctor_id == history.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.consultation_id = history.consultation_id
        row.body = history.body
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, history_id: UUID) -> bool:
        stmt = delete(MedicalHistoryModel).where(
            MedicalHistoryModel.id == history_id,
            MedicalHistoryModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
