from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.consultation import Consultation


class ConsultationRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Consultation]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, consultation: Consultation) -> Consultation:
        raise NotImplementedError
