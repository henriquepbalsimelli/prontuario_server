from datetime import datetime
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.consultation_repository import ConsultationRepository
from app.domain.models.consultation import (
    CONSULTATION_STATUS_CANCELLED,
    Consultation,
)
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
            scheduled_start_at=model.scheduled_start_at,
            scheduled_end_at=model.scheduled_end_at,
            status=model.status,
            diagnosis=model.diagnosis,
            notes=model.notes,
            chief_complaint=model.chief_complaint,
            physical_exam=model.physical_exam,
            conduct=model.conduct,
            created_at=model.created_at,
        )

    async def get_by_id(
        self,
        doctor_id: UUID,
        consultation_id: UUID,
        patient_id: UUID | None = None,
    ) -> Consultation | None:
        stmt = select(ConsultationModel).where(
            ConsultationModel.id == consultation_id,
            ConsultationModel.doctor_id == doctor_id,
        )
        if patient_id is not None:
            stmt = stmt.where(ConsultationModel.patient_id == patient_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

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
            .order_by(
                case((ConsultationModel.consultation_date.is_(None), 1), else_=0).asc(),
                ConsultationModel.consultation_date.desc(),
                ConsultationModel.created_at.desc(),
            )
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
            scheduled_start_at=consultation.scheduled_start_at,
            scheduled_end_at=consultation.scheduled_end_at,
            status=consultation.status,
            diagnosis=consultation.diagnosis,
            notes=consultation.notes,
            chief_complaint=consultation.chief_complaint,
            physical_exam=consultation.physical_exam,
            conduct=consultation.conduct,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, consultation: Consultation) -> Consultation:
        stmt = select(ConsultationModel).where(
            ConsultationModel.id == consultation.id,
            ConsultationModel.doctor_id == consultation.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()

        row.consultation_date = consultation.consultation_date
        row.scheduled_start_at = consultation.scheduled_start_at
        row.scheduled_end_at = consultation.scheduled_end_at
        row.status = consultation.status
        row.diagnosis = consultation.diagnosis
        row.notes = consultation.notes
        row.chief_complaint = consultation.chief_complaint
        row.physical_exam = consultation.physical_exam
        row.conduct = consultation.conduct

        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def list_by_doctor_interval(
        self,
        doctor_id: UUID,
        start_at: datetime,
        end_at: datetime,
        status: str | None,
    ) -> list[Consultation]:
        stmt = select(ConsultationModel).where(
            ConsultationModel.doctor_id == doctor_id,
            ConsultationModel.scheduled_start_at.is_not(None),
            ConsultationModel.scheduled_end_at.is_not(None),
            ConsultationModel.scheduled_start_at < end_at,
            ConsultationModel.scheduled_end_at > start_at,
        )
        if status is not None:
            stmt = stmt.where(ConsultationModel.status == status)
        stmt = stmt.order_by(ConsultationModel.scheduled_start_at.asc(), ConsultationModel.created_at.asc())
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def has_schedule_overlap(
        self,
        doctor_id: UUID,
        scheduled_start_at: datetime,
        scheduled_end_at: datetime,
        exclude_consultation_id: UUID | None = None,
    ) -> bool:
        stmt = select(ConsultationModel.id).where(
            ConsultationModel.doctor_id == doctor_id,
            ConsultationModel.scheduled_start_at.is_not(None),
            ConsultationModel.scheduled_end_at.is_not(None),
            ConsultationModel.status != CONSULTATION_STATUS_CANCELLED,
            ConsultationModel.scheduled_start_at < scheduled_end_at,
            ConsultationModel.scheduled_end_at > scheduled_start_at,
        )
        if exclude_consultation_id is not None:
            stmt = stmt.where(ConsultationModel.id != exclude_consultation_id)
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def get_latest_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> Consultation | None:
        stmt = (
            select(ConsultationModel)
            .where(
                ConsultationModel.doctor_id == doctor_id,
                ConsultationModel.patient_id == patient_id,
            )
            .order_by(
                case((ConsultationModel.consultation_date.is_(None), 1), else_=0).asc(),
                ConsultationModel.consultation_date.desc(),
                ConsultationModel.created_at.desc(),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)
