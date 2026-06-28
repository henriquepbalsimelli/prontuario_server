from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.evolution_service import (
    CreateEvolutionInput,
    EvolutionConsultationNotFoundError,
    EvolutionNotFoundError,
    EvolutionPatientNotFoundError,
    EvolutionService,
    EvolutionValidationError,
    UpdateEvolutionInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_evolution_service
from app.presentation.schemas.evolution_schema import (
    EvolutionCreateRequest,
    EvolutionResponse,
    EvolutionUpdateRequest,
)

router = APIRouter(tags=["evolutions"])


@router.post("/patients/{patient_id}/evolutions", response_model=EvolutionResponse, status_code=status.HTTP_201_CREATED)
async def create_evolution(
    patient_id: UUID,
    payload: EvolutionCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: EvolutionService = Depends(get_evolution_service),
) -> EvolutionResponse:
    try:
        evolution = await service.create_evolution(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            payload=CreateEvolutionInput(**payload.model_dump()),
        )
    except EvolutionPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvolutionConsultationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvolutionValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return EvolutionResponse.model_validate(evolution)


@router.get("/patients/{patient_id}/evolutions", response_model=list[EvolutionResponse])
async def list_evolutions(
    patient_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: EvolutionService = Depends(get_evolution_service),
) -> list[EvolutionResponse]:
    try:
        evolutions = await service.list_evolutions(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )
    except EvolutionPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [EvolutionResponse.model_validate(item) for item in evolutions]


@router.get("/evolutions/{evolution_id}", response_model=EvolutionResponse)
async def get_evolution(
    evolution_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: EvolutionService = Depends(get_evolution_service),
) -> EvolutionResponse:
    try:
        evolution = await service.get_evolution(
            doctor_id=doctor.doctor_id,
            evolution_id=evolution_id,
        )
    except EvolutionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return EvolutionResponse.model_validate(evolution)


@router.put("/evolutions/{evolution_id}", response_model=EvolutionResponse)
async def update_evolution(
    evolution_id: UUID,
    payload: EvolutionUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: EvolutionService = Depends(get_evolution_service),
) -> EvolutionResponse:
    try:
        evolution = await service.update_evolution(
            doctor_id=doctor.doctor_id,
            evolution_id=evolution_id,
            payload=UpdateEvolutionInput(**payload.model_dump()),
        )
    except EvolutionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvolutionConsultationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvolutionValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return EvolutionResponse.model_validate(evolution)
