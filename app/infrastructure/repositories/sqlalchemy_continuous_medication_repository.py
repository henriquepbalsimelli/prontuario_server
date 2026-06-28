from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.continuous_medication_repository import ContinuousMedicationRepository
from app.domain.models.continuous_medication import ContinuousMedication
from app.infrastructure.database.models import (
    PatientContinuousMedication as ContinuousMedicationModel,
)


class SQLAlchemyContinuousMedicationRepository(ContinuousMedicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ContinuousMedicationModel) -> ContinuousMedication:
        return ContinuousMedication(
            id=model.id,
            doctor_id=model.doctor_id,
            patient_id=model.patient_id,
            consultation_id=model.consultation_id,
            name=model.name,
            dosage=model.dosage,
            notes=model.notes,
            status=model.status,
            created_at=model.created_at,
        )

    async def list_by_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        consultation_id: UUID | None = None,
    ) -> list[ContinuousMedication]:
        stmt = select(ContinuousMedicationModel).where(
            ContinuousMedicationModel.doctor_id == doctor_id,
            ContinuousMedicationModel.patient_id == patient_id,
        )
        if consultation_id is not None:
            stmt = stmt.where(ContinuousMedicationModel.consultation_id == consultation_id)
        if status is not None:
            stmt = stmt.where(ContinuousMedicationModel.status == status)
        stmt = stmt.order_by(ContinuousMedicationModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def list_by_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        consultation_id: UUID,
        status: str | None = None,
    ) -> list[ContinuousMedication]:
        return await self.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status=status,
            consultation_id=consultation_id,
        )

    async def get_by_id(self, doctor_id: UUID, medication_id: UUID) -> ContinuousMedication | None:
        stmt = select(ContinuousMedicationModel).where(
            ContinuousMedicationModel.id == medication_id,
            ContinuousMedicationModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else self._to_domain(row)

    async def create(self, medication: ContinuousMedication) -> ContinuousMedication:
        row = ContinuousMedicationModel(
            id=medication.id,
            doctor_id=medication.doctor_id,
            patient_id=medication.patient_id,
            consultation_id=medication.consultation_id,
            name=medication.name,
            dosage=medication.dosage,
            notes=medication.notes,
            status=medication.status,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def update(self, medication: ContinuousMedication) -> ContinuousMedication:
        stmt = select(ContinuousMedicationModel).where(
            ContinuousMedicationModel.id == medication.id,
            ContinuousMedicationModel.doctor_id == medication.doctor_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        row.consultation_id = medication.consultation_id
        row.name = medication.name
        row.dosage = medication.dosage
        row.notes = medication.notes
        row.status = medication.status
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_domain(row)

    async def delete(self, doctor_id: UUID, medication_id: UUID) -> bool:
        stmt = delete(ContinuousMedicationModel).where(
            ContinuousMedicationModel.id == medication_id,
            ContinuousMedicationModel.doctor_id == doctor_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
