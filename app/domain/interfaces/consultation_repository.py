from datetime import datetime
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.consultation import Consultation


class ConsultationRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        doctor_id: UUID,
        consultation_id: UUID,
        patient_id: UUID | None = None,
    ) -> Consultation | None:
        raise NotImplementedError

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

    @abstractmethod
    async def update(self, consultation: Consultation) -> Consultation:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> Consultation | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_doctor_interval(
        self,
        doctor_id: UUID,
        start_at: datetime,
        end_at: datetime,
        status: str | None,
    ) -> list[Consultation]:
        raise NotImplementedError

    @abstractmethod
    async def has_schedule_overlap(
        self,
        doctor_id: UUID,
        scheduled_start_at: datetime,
        scheduled_end_at: datetime,
        exclude_consultation_id: UUID | None = None,
    ) -> bool:
        raise NotImplementedError
