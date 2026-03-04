from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.lesion_service import (
    CreateLesionInput,
    LesionNotFoundError,
    LesionPatientNotFoundError,
    LesionService,
    UpdateLesionInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_lesion_service
from app.presentation.schemas.lesion_schema import (
    LesionCreateRequest,
    LesionResponse,
    LesionUpdateRequest,
)

router = APIRouter(tags=["lesions"])


@router.post("/patients/{patient_id}/lesions", response_model=LesionResponse, status_code=status.HTTP_201_CREATED)
async def create_lesion(
    patient_id: UUID,
    payload: LesionCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: LesionService = Depends(get_lesion_service),
) -> LesionResponse:
    try:
        lesion = await service.create_lesion(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            payload=CreateLesionInput(**payload.model_dump()),
        )
    except LesionPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LesionResponse.model_validate(lesion)


@router.get("/patients/{patient_id}/lesions", response_model=list[LesionResponse])
async def list_patient_lesions(
    patient_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: LesionService = Depends(get_lesion_service),
) -> list[LesionResponse]:
    try:
        lesions = await service.list_lesions(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )
    except LesionPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [LesionResponse.model_validate(item) for item in lesions]


@router.put("/lesions/{lesion_id}", response_model=LesionResponse)
async def update_lesion(
    lesion_id: UUID,
    payload: LesionUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: LesionService = Depends(get_lesion_service),
) -> LesionResponse:
    try:
        lesion = await service.update_lesion(
            doctor_id=doctor.doctor_id,
            lesion_id=lesion_id,
            payload=UpdateLesionInput(**payload.model_dump()),
        )
    except LesionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LesionResponse.model_validate(lesion)
