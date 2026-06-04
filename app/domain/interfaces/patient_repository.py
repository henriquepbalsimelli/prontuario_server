from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.patient import Patient


class PatientRepository(ABC):
    @abstractmethod
    async def list_by_doctor(
        self,
        doctor_id: UUID,
        page: int,
        page_size: int,
        name: str | None = None,
    ) -> list[Patient]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, patient_id: UUID) -> Patient | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        raise NotImplementedError

    @abstractmethod
    async def update(self, patient: Patient) -> Patient:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, patient_id: UUID) -> bool:
        raise NotImplementedError
