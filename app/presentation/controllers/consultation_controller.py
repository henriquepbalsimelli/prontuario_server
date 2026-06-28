from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.consultation_service import (
    ConsultationMedicationInput,
    ConsultationCopySourceNotFoundError,
    ConsultationNotFoundError,
    ConsultationPatientNotFoundError,
    ConsultationScheduleConflictError,
    ConsultationService,
    ConsultationValidationError,
    CreateConsultationInput,
    UpdateConsultationInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_consultation_service
from app.presentation.schemas.consultation_schema import (
    ConsultationCreateRequest,
    ConsultationResponse,
    ConsultationUpdateRequest,
)
from app.presentation.schemas.evolution_schema import EvolutionResponse

router = APIRouter(prefix="/patients/{patient_id}/consultations", tags=["consultations"])
detail_router = APIRouter(tags=["consultations"])


@detail_router.get("/consultations", response_model=list[ConsultationResponse])
async def list_consultations_by_interval(
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    status_filter: str | None = Query(default=None, alias="status"),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> list[ConsultationResponse]:
    try:
        consultations = await service.list_consultations_by_interval(
            doctor_id=doctor.doctor_id,
            start_at=start_at,
            end_at=end_at,
            status=status_filter,
        )
    except ConsultationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return [ConsultationResponse.model_validate(item) for item in consultations]


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
            payload=CreateConsultationInput(
                **{
                    **payload.model_dump(exclude={"continuous_medications"}),
                    "continuous_medications": [
                        ConsultationMedicationInput(**item.model_dump())
                        for item in payload.continuous_medications
                    ],
                }
            ),
        )
    except ConsultationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConsultationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ConsultationScheduleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConsultationResponse.model_validate(consultation)


@router.post("/copy-latest", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def copy_latest_consultation(
    patient_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationResponse:
    try:
        consultation = await service.copy_latest_consultation(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
        )
    except ConsultationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConsultationCopySourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConsultationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ConsultationScheduleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConsultationResponse.model_validate(consultation)


@detail_router.get("/consultations/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationResponse:
    try:
        consultation = await service.get_consultation(
            doctor_id=doctor.doctor_id,
            consultation_id=consultation_id,
        )
    except ConsultationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ConsultationResponse.model_validate(consultation)


@detail_router.put("/consultations/{consultation_id}", response_model=ConsultationResponse)
async def update_consultation(
    consultation_id: UUID,
    payload: ConsultationUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationResponse:
    try:
        consultation = await service.update_consultation(
            doctor_id=doctor.doctor_id,
            consultation_id=consultation_id,
            payload=UpdateConsultationInput(
                fields={
                    **payload.model_dump(
                        exclude_unset=True,
                        exclude={"continuous_medications"},
                    ),
                    **(
                        {
                            "continuous_medications": [
                                ConsultationMedicationInput(**item.model_dump())
                                for item in payload.continuous_medications
                            ]
                        }
                        if "continuous_medications" in payload.model_fields_set
                        else {}
                    ),
                }
            ),
        )
    except ConsultationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConsultationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ConsultationScheduleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ConsultationResponse.model_validate(consultation)


@detail_router.get(
    "/consultations/{consultation_id}/evolutions",
    response_model=list[EvolutionResponse],
)
async def list_consultation_evolutions(
    consultation_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ConsultationService = Depends(get_consultation_service),
) -> list[EvolutionResponse]:
    try:
        evolutions = await service.list_consultation_evolutions(
            doctor_id=doctor.doctor_id,
            consultation_id=consultation_id,
            page=page,
            page_size=page_size,
        )
    except ConsultationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [EvolutionResponse.model_validate(item) for item in evolutions]
