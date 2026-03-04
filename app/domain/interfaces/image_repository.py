from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.image import Image


class ImageRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Image]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, image: Image) -> Image:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, image_id: UUID) -> Image | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_uploaded(
        self,
        doctor_id: UUID,
        image_id: UUID,
        file_size_bytes: int | None,
        etag: str | None,
    ) -> Image | None:
        raise NotImplementedError
