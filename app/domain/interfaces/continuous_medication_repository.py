from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.continuous_medication import ContinuousMedication


class ContinuousMedicationRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
    ) -> list[ContinuousMedication]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
        status: str | None = None,
    ) -> list[ContinuousMedication]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, medication_id: UUID) -> ContinuousMedication | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, medication: ContinuousMedication) -> ContinuousMedication:
        raise NotImplementedError

    @abstractmethod
    async def update(self, medication: ContinuousMedication) -> ContinuousMedication:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, medication_id: UUID) -> bool:
        raise NotImplementedError
