from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.services.continuous_medication_service import (
    ContinuousMedicationNotFoundError,
    ContinuousMedicationPatientNotFoundError,
    ContinuousMedicationService,
    ContinuousMedicationValidationError,
    CreateContinuousMedicationInput,
    UpdateContinuousMedicationInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_continuous_medication_service
from app.presentation.schemas.continuous_medication_schema import (
    ContinuousMedicationCreateRequest,
    ContinuousMedicationResponse,
    ContinuousMedicationUpdateRequest,
)

router = APIRouter(tags=["continuous_medications"])


@router.get("/patients/{patient_id}/continuous-medications", response_model=list[ContinuousMedicationResponse])
async def list_continuous_medications(
    patient_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    consultation_id: UUID | None = Query(default=None),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ContinuousMedicationService = Depends(get_continuous_medication_service),
) -> list[ContinuousMedicationResponse]:
    try:
        items = await service.list_medications(
            doctor.doctor_id,
            patient_id,
            status_filter,
            consultation_id,
        )
    except ContinuousMedicationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ContinuousMedicationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [ContinuousMedicationResponse.model_validate(item) for item in items]


@router.post("/patients/{patient_id}/continuous-medications", response_model=ContinuousMedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_continuous_medication(
    patient_id: UUID,
    payload: ContinuousMedicationCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ContinuousMedicationService = Depends(get_continuous_medication_service),
) -> ContinuousMedicationResponse:
    try:
        item = await service.create_medication(
            doctor.doctor_id,
            patient_id,
            CreateContinuousMedicationInput(**payload.model_dump()),
        )
    except ContinuousMedicationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ContinuousMedicationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ContinuousMedicationResponse.model_validate(item)


@router.put("/continuous-medications/{medication_id}", response_model=ContinuousMedicationResponse)
async def update_continuous_medication(
    medication_id: UUID,
    payload: ContinuousMedicationUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ContinuousMedicationService = Depends(get_continuous_medication_service),
) -> ContinuousMedicationResponse:
    try:
        item = await service.update_medication(
            doctor.doctor_id,
            medication_id,
            UpdateContinuousMedicationInput(**payload.model_dump()),
        )
    except ContinuousMedicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ContinuousMedicationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ContinuousMedicationResponse.model_validate(item)


@router.delete("/continuous-medications/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_continuous_medication(
    medication_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ContinuousMedicationService = Depends(get_continuous_medication_service),
) -> Response:
    try:
        await service.delete_medication(doctor.doctor_id, medication_id)
    except ContinuousMedicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
