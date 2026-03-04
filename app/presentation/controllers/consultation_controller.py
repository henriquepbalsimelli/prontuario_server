from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.consultation_service import (
    ConsultationPatientNotFoundError,
    ConsultationService,
    CreateConsultationInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_consultation_service
from app.presentation.schemas.consultation_schema import (
    ConsultationCreateRequest,
    ConsultationResponse,
)

router = APIRouter(prefix="/patients/{patient_id}/consultations", tags=["consultations"])


@router.get("", response_model=list[ConsultationResponse])
async def list_consultations(
    patient_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> list[ConsultationResponse]:
    try:
        consultations = await service.list_consultations(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )
    except ConsultationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ConsultationResponse.model_validate(item) for item in consultations]


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    patient_id: UUID,
    payload: ConsultationCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationResponse:
    try:
        consultation = await service.create_consultation(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            payload=CreateConsultationInput(**payload.model_dump()),
        )
    except ConsultationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ConsultationResponse.model_validate(consultation)
