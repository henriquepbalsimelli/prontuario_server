from abc import ABC, abstractmethod

from uuid import UUID

from app.domain.models.doctor import Doctor


class DoctorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, doctor_id: UUID) -> Doctor | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Doctor | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, doctor: Doctor) -> Doctor:
        raise NotImplementedError

    @abstractmethod
    async def update_preferences(self, doctor_id: UUID, preferences: dict) -> Doctor | None:
        raise NotImplementedError
