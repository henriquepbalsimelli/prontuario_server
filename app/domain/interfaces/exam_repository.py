from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.models.exam import Exam


class ExamRepository(ABC):
    @abstractmethod
    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Exam]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, doctor_id: UUID, exam_id: UUID) -> Exam | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, exam: Exam) -> Exam:
        raise NotImplementedError

    @abstractmethod
    async def update(self, exam: Exam) -> Exam:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doctor_id: UUID, exam_id: UUID) -> bool:
        raise NotImplementedError
