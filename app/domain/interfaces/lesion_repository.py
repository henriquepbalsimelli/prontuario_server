from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.lesion import Lesion


class LesionRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Lesion]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, lesion_id: UUID) -> Lesion | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, lesion: Lesion) -> Lesion:
        raise NotImplementedError

    @abstractmethod
    async def update(self, lesion: Lesion) -> Lesion:
        raise NotImplementedError
