from fastapi import APIRouter, Depends, Query, status

from app.application.services.medication_service import (
    CreateMedicationInput,
    MedicationService,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_medication_service
from app.presentation.schemas.medication_schema import (
    MedicationCreateRequest,
    MedicationResponse,
)

router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("", response_model=list[MedicationResponse])
async def list_medications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicationService = Depends(get_medication_service),
) -> list[MedicationResponse]:
    medications = await service.list_medications(page=page, page_size=page_size)
    return [MedicationResponse.model_validate(item) for item in medications]


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    payload: MedicationCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    medication = await service.create_medication(
        actor_doctor_id=doctor.doctor_id,
        payload=CreateMedicationInput(**payload.model_dump())
    )
    return MedicationResponse.model_validate(medication)
