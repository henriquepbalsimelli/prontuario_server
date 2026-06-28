from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.medical_history import MedicalHistory


class MedicalHistoryRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID | None = None,
    ) -> list[MedicalHistory]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, history_id: UUID) -> MedicalHistory | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_for_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> MedicalHistory | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_for_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
    ) -> MedicalHistory | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, history: MedicalHistory) -> MedicalHistory:
        raise NotImplementedError

    @abstractmethod
    async def update(self, history: MedicalHistory) -> MedicalHistory:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, history_id: UUID) -> bool:
        raise NotImplementedError
