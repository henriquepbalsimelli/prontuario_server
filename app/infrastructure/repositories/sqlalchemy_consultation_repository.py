from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.models.consultation import Consultation
from app.infrastructure.database.models import Consultation as ConsultationModel


class SQLAlchemyConsultationRepository(ConsultationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ConsultationModel) -> Consultation:
        return Consultation(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_date=model.consultation_date,
            chief_complaint=model.chief_complaint,
            physical_exam=model.physical_exam,
            conduct=model.conduct,
            created_at=model.created_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Consultation]:
        offset = (page - 1) * page_size
        stmt = (
            select(ConsultationModel)
            .where(
                ConsultationModel.doctor_id == doctor_id,
                ConsultationModel.patient_id == patient_id,
            )
            .order_by(ConsultationModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def create(self, consultation: Consultation) -> Consultation:
        row = ConsultationModel(
            id=consultation.id,
            doctor_id=consultation.doctor_id,
            patient_id=consultation.patient_id,
            consultation_date=consultation.consultation_date,
            chief_complaint=consultation.chief_complaint,
            physical_exam=consultation.physical_exam,
            conduct=consultation.conduct,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)
