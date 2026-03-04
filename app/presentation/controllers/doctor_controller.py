from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.doctor_service import (
    CreateDoctorInput,
    DoctorEmailAlreadyExistsError,
    DoctorService,
)
from app.presentation.dependencies import get_doctor_service
from app.presentation.schemas.doctor_schema import DoctorCreateRequest, DoctorResponse

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
