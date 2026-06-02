from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.doctor_service import (
    CreateDoctorInput,
    DoctorEmailAlreadyExistsError,
    DoctorNotFoundError,
    DoctorService,
    UpdateDoctorPreferencesInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_doctor_service
from app.presentation.schemas.doctor_schema import (
    DoctorCreateRequest,
    DoctorPreferencesRequest,
    DoctorPreferencesResponse,
    DoctorResponse,
)

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    payload: DoctorCreateRequest,
    service: DoctorService = Depends(get_doctor_service),
) -> DoctorResponse:
    try:
        doctor = await service.create_doctor(payload=CreateDoctorInput(**payload.model_dump()))
    except DoctorEmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return DoctorResponse.model_validate(doctor)


@router.put(
    "/{doctor_id}/preferences",
    response_model=DoctorPreferencesResponse,
    status_code=status.HTTP_200_OK,
)
async def update_doctor_preferences(
    doctor_id: UUID,
    payload: DoctorPreferencesRequest,
    service: DoctorService = Depends(get_doctor_service),
    authenticated_doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
) -> DoctorPreferencesResponse:
    if authenticated_doctor.doctor_id != doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor preferences can only be updated by the owner",
        )

    try:
        doctor = await service.update_preferences(
            doctor_id=doctor_id,
            payload=UpdateDoctorPreferencesInput(preferences=payload.model_dump()),
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DoctorPreferencesResponse(
        doctor_id=doctor.id,
        preferences=doctor.preferences,
    )
