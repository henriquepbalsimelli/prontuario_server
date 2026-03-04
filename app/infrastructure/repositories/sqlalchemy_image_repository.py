from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.image_repository import ImageRepository
from app.domain.models.image import Image
from app.infrastructure.database.models import Image as ImageModel


class SQLAlchemyImageRepository(ImageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ImageModel) -> Image:
        return Image(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            s3_key=model.s3_key,
            type=model.type,
            body_region=model.body_region,
            coord_x=model.coord_x,
            coord_y=model.coord_y,
            upload_status=model.upload_status,
            uploaded_at=model.uploaded_at,
            file_size_bytes=model.file_size_bytes,
            etag=model.etag,
            created_at=model.created_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Image]:
        offset = (page - 1) * page_size
        stmt = (
            select(ImageModel)
            .where(ImageModel.doctor_id == doctor_id, ImageModel.patient_id == patient_id)
            .order_by(ImageModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def create(self, image: Image) -> Image:
        row = ImageModel(
            id=image.id,
            doctor_id=image.doctor_id,
            patient_id=image.patient_id,
            consultation_id=image.consultation_id,
            s3_key=image.s3_key,
            type=image.type,
            body_region=image.body_region,
            coord_x=image.coord_x,
            coord_y=image.coord_y,
            upload_status=image.upload_status,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def get_by_id(self, doctor_id: UUID, image_id: UUID) -> Image | None:
        stmt = select(ImageModel).where(
            ImageModel.id == image_id,
            ImageModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def mark_uploaded(
        self,
        doctor_id: UUID,
        image_id: UUID,
        file_size_bytes: int | None,
        etag: str | None,
    ) -> Image | None:
        stmt = select(ImageModel).where(
            ImageModel.id == image_id,
            ImageModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None

        row.upload_status = "uploaded"
        row.uploaded_at = func.now()
        row.file_size_bytes = file_size_bytes
        row.etag = etag

        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)
