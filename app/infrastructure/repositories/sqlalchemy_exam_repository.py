from datetime import date
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.exam_repository import ExamRepository
from app.domain.models.exam import Exam
from app.infrastructure.database.models import Exam as ExamModel


class SQLAlchemyExamRepository(ExamRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ExamModel) -> Exam:
        return Exam(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            name=model.name,
            type=model.type,
            exam_date=model.exam_date,
            status=model.status,
            result_notes=model.result_notes,
            created_at=model.created_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Exam]:
        stmt = select(ExamModel).where(
            ExamModel.doctor_id == doctor_id,
            ExamModel.patient_id == patient_id,
        )
        if status is not None:
            stmt = stmt.where(ExamModel.status == status)
        if consultation_id is not None:
            stmt = stmt.where(ExamModel.consultation_id == consultation_id)
        if start_date is not None:
            stmt = stmt.where(ExamModel.exam_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(ExamModel.exam_date <= end_date)
        stmt = stmt.order_by(ExamModel.exam_date.desc(), ExamModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_by_id(self, doctor_id: UUID, exam_id: UUID) -> Exam | None:
        stmt = select(ExamModel).where(
            ExamModel.id == exam_id,
            ExamModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, exam: Exam) -> Exam:
        row = ExamModel(
            id=exam.id,
            doctor_id=exam.doctor_id,
            patient_id=exam.patient_id,
            consultation_id=exam.consultation_id,
            name=exam.name,
            type=exam.type,
            exam_date=exam.exam_date,
            status=exam.status,
            result_notes=exam.result_notes,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, exam: Exam) -> Exam:
        stmt = select(ExamModel).where(
            ExamModel.id == exam.id,
            ExamModel.doctor_id == exam.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.consultation_id = exam.consultation_id
        row.name = exam.name
        row.type = exam.type
        row.exam_date = exam.exam_date
        row.status = exam.status
        row.result_notes = exam.result_notes
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, exam_id: UUID) -> bool:
        stmt = delete(ExamModel).where(
            ExamModel.id == exam_id,
            ExamModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
