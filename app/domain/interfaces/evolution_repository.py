from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.evolution import Evolution


class EvolutionRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, evolution_id: UUID) -> Evolution | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Evolution]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, evolution: Evolution) -> Evolution:
        raise NotImplementedError

    @abstractmethod
    async def update(self, evolution: Evolution) -> Evolution:
        raise NotImplementedError
