from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.doctor_template import DoctorTemplate


class DoctorTemplateRepository(ABC):
    @abstractmethod
    async def list_by_doctor(self, doctor_id: UUID, template_type: str | None = None) -> list[DoctorTemplate]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, template_id: UUID) -> DoctorTemplate | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, template: DoctorTemplate) -> DoctorTemplate:
        raise NotImplementedError

    @abstractmethod
    async def update(self, template: DoctorTemplate) -> DoctorTemplate:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, template_id: UUID) -> bool:
        raise NotImplementedError
