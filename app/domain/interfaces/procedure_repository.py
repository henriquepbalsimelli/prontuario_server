from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.procedure import Procedure


class ProcedureRepository(ABC):
    @abstractmethod
    async def list_by_patient(self, doctor_id: UUID, patient_id: UUID) -> list[Procedure]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, procedure_id: UUID) -> Procedure | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, procedure: Procedure) -> Procedure:
        raise NotImplementedError

    @abstractmethod
    async def update(self, procedure: Procedure) -> Procedure:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, procedure_id: UUID) -> bool:
        raise NotImplementedError
