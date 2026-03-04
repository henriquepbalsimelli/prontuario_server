from abc import ABC, abstractmethod

from app.domain.models.medication import Medication


class MedicationRepository(ABC):
    @abstractmethod
    async def list_all(self, page: int, page_size: int) -> list[Medication]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, medication: Medication) -> Medication:
        raise NotImplementedError
