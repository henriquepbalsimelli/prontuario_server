from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.doctor_template_repository import DoctorTemplateRepository
from app.domain.models.doctor_template import DoctorTemplate
from app.infrastructure.database.models import DoctorTemplate as DoctorTemplateModel


class SQLAlchemyDoctorTemplateRepository(DoctorTemplateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: DoctorTemplateModel) -> DoctorTemplate:
        return DoctorTemplate(
            id=model.id,
            doctor_id=model.doctor_id,
            title=model.title,
            type=model.type,
            body=model.body,
            created_at=model.created_at,
        )

    async def list_by_doctor(self, doctor_id: UUID, template_type: str | None = None) -> list[DoctorTemplate]:
        stmt = select(DoctorTemplateModel).where(DoctorTemplateModel.doctor_id == doctor_id)
        if template_type is not None:
            stmt = stmt.where(DoctorTemplateModel.type == template_type)
        stmt = stmt.order_by(DoctorTemplateModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_by_id(self, doctor_id: UUID, template_id: UUID) -> DoctorTemplate | None:
        stmt = select(DoctorTemplateModel).where(
            DoctorTemplateModel.id == template_id,
            DoctorTemplateModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, template: DoctorTemplate) -> DoctorTemplate:
        row = DoctorTemplateModel(
            id=template.id,
            doctor_id=template.doctor_id,
            title=template.title,
            type=template.type,
            body=template.body,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, template: DoctorTemplate) -> DoctorTemplate:
        stmt = select(DoctorTemplateModel).where(
            DoctorTemplateModel.id == template.id,
            DoctorTemplateModel.doctor_id == template.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.title = template.title
        row.type = template.type
        row.body = template.body
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, template_id: UUID) -> bool:
        stmt = delete(DoctorTemplateModel).where(
            DoctorTemplateModel.id == template_id,
            DoctorTemplateModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
