from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.services.medical_history_service import (
    CreateMedicalHistoryInput,
    MedicalHistoryNotFoundError,
    MedicalHistoryPatientNotFoundError,
    MedicalHistoryService,
    MedicalHistoryValidationError,
    UpdateMedicalHistoryInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_medical_history_service
from app.presentation.schemas.medical_history_schema import (
    MedicalHistoryCreateRequest,
    MedicalHistoryResponse,
    MedicalHistoryUpdateRequest,
)

router = APIRouter(tags=["medical_histories"])


@router.get("/patients/{patient_id}/medical-histories", response_model=list[MedicalHistoryResponse])
async def list_medical_histories(
    patient_id: UUID,
    consultation_id: UUID | None = Query(default=None),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicalHistoryService = Depends(get_medical_history_service),
) -> list[MedicalHistoryResponse]:
    try:
        items = await service.list_histories(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            consultation_id=consultation_id,
        )
    except MedicalHistoryPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MedicalHistoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [MedicalHistoryResponse.model_validate(item) for item in items]


@router.post("/patients/{patient_id}/medical-histories", response_model=MedicalHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_history(
    patient_id: UUID,
    payload: MedicalHistoryCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicalHistoryService = Depends(get_medical_history_service),
) -> MedicalHistoryResponse:
    try:
        item = await service.create_history(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            payload=CreateMedicalHistoryInput(**payload.model_dump()),
        )
    except MedicalHistoryPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MedicalHistoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return MedicalHistoryResponse.model_validate(item)


@router.put("/medical-histories/{history_id}", response_model=MedicalHistoryResponse)
async def update_medical_history(
    history_id: UUID,
    payload: MedicalHistoryUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicalHistoryService = Depends(get_medical_history_service),
) -> MedicalHistoryResponse:
    try:
        item = await service.update_history(
            doctor_id=doctor.doctor_id,
            history_id=history_id,
            payload=UpdateMedicalHistoryInput(**payload.model_dump()),
        )
    except MedicalHistoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MedicalHistoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return MedicalHistoryResponse.model_validate(item)


@router.delete("/medical-histories/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_history(
    history_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: MedicalHistoryService = Depends(get_medical_history_service),
) -> Response:
    try:
        await service.delete_history(doctor_id=doctor.doctor_id, history_id=history_id)
    except MedicalHistoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
