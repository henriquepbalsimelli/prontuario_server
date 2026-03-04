from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.doctor_repository import DoctorRepository
from app.domain.models.doctor import Doctor
from app.infrastructure.database.models import Doctor as DoctorModel


class SQLAlchemyDoctorRepository(DoctorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: DoctorModel) -> Doctor:
        return Doctor(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )

    async def get_by_email(self, email: str) -> Doctor | None:
        stmt = select(DoctorModel).where(DoctorModel.email == email)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def create(self, doctor: Doctor) -> Doctor:
        row = DoctorModel(
            id=doctor.id,
            name=doctor.name,
            email=doctor.email,
            password_hash=doctor.password_hash,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)
