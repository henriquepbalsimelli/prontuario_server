from abc import ABC, abstractmethod

from app.domain.models.disease import Disease


class DiseaseRepository(ABC):
    @abstractmethod
    async def list_all(self, page: int, page_size: int) -> list[Disease]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, disease: Disease) -> Disease:
        raise NotImplementedError
