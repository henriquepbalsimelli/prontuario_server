from abc import ABC, abstractmethod

from app.domain.models.doctor import Doctor


class DoctorRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Doctor | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, doctor: Doctor) -> Doctor:
        raise NotImplementedError
