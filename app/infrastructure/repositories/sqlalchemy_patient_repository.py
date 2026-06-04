from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.patient import Patient
from app.infrastructure.database.models import Patient as PatientModel


class SQLAlchemyPatientRepository(PatientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: PatientModel) -> Patient:
        return Patient(
            id=model.id,
            doctor_id=model.doctor_id,
            name=model.name,
            birth_date=model.birth_date,
            gender=model.gender,
            phone=model.phone,
            notes=model.notes,
            created_at=model.created_at,
        )

    async def list_by_doctor(
        self,
        doctor_id: UUID,
        page: int,
        page_size: int,
        name: str | None = None,
    ) -> list[Patient]:
        offset = (page - 1) * page_size
        stmt = select(PatientModel).where(PatientModel.doctor_id == doctor_id)

        if name is not None:
            stmt = stmt.where(
                PatientModel.name.ilike(f"%{name}%")
            ).order_by(PatientModel.name.asc())
        else:
            stmt = stmt.order_by(PatientModel.created_at.desc())

        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, doctor_id: UUID, patient_id: UUID) -> Patient | None:
        stmt = select(PatientModel).where(
            PatientModel.id == patient_id,
            PatientModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def create(self, patient: Patient) -> Patient:
        row = PatientModel(
            id=patient.id,
            doctor_id=patient.doctor_id,
            name=patient.name,
            birth_date=patient.birth_date,
            gender=patient.gender,
            phone=patient.phone,
            notes=patient.notes,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, patient: Patient) -> Patient:
        stmt = select(PatientModel).where(
            PatientModel.id == patient.id,
            PatientModel.doctor_id == patient.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()

        row.name = patient.name
        row.birth_date = patient.birth_date
        row.gender = patient.gender
        row.phone = patient.phone
        row.notes = patient.notes

        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, patient_id: UUID) -> bool:
        stmt = delete(PatientModel).where(
            PatientModel.id == patient_id,
            PatientModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
