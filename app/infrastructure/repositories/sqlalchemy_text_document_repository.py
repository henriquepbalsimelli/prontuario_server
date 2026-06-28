from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.text_document_repository import TextDocumentRepository
from app.domain.models.text_document import TextDocument
from app.infrastructure.database.models import TextDocument as TextDocumentModel


class SQLAlchemyTextDocumentRepository(TextDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: TextDocumentModel) -> TextDocument:
        return TextDocument(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            template_id=model.template_id,
            type=model.type,
            title=model.title,
            body=model.body,
            version=model.version,
            created_at=model.created_at,
        )

    async def list_by_patient(self, doctor_id: UUID, patient_id: UUID) -> list[TextDocument]:
        stmt = (
            select(TextDocumentModel)
            .where(
                TextDocumentModel.doctor_id == doctor_id,
                TextDocumentModel.patient_id == patient_id,
            )
            .order_by(TextDocumentModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_by_id(self, doctor_id: UUID, document_id: UUID) -> TextDocument | None:
        stmt = select(TextDocumentModel).where(
            TextDocumentModel.id == document_id,
            TextDocumentModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, document: TextDocument) -> TextDocument:
        row = TextDocumentModel(
            id=document.id,
            doctor_id=document.doctor_id,
            patient_id=document.patient_id,
            consultation_id=document.consultation_id,
            template_id=document.template_id,
            type=document.type,
            title=document.title,
            body=document.body,
            version=document.version,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, document: TextDocument) -> TextDocument:
        stmt = select(TextDocumentModel).where(
            TextDocumentModel.id == document.id,
            TextDocumentModel.doctor_id == document.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.consultation_id = document.consultation_id
        row.template_id = document.template_id
        row.type = document.type
        row.title = document.title
        row.body = document.body
        row.version = document.version
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, document_id: UUID) -> bool:
        stmt = delete(TextDocumentModel).where(
            TextDocumentModel.id == document_id,
            TextDocumentModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
