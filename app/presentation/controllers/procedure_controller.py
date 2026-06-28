from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.services.procedure_service import (
    CreateProcedureInput,
    ProcedureNotFoundError,
    ProcedurePatientNotFoundError,
    ProcedureService,
    ProcedureValidationError,
    UpdateProcedureInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_procedure_service
from app.presentation.schemas.procedure_schema import (
    ProcedureCreateRequest,
    ProcedureResponse,
    ProcedureUpdateRequest,
)

router = APIRouter(tags=["procedures"])


@router.get("/patients/{patient_id}/procedures", response_model=list[ProcedureResponse])
async def list_procedures(
    patient_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ProcedureService = Depends(get_procedure_service),
) -> list[ProcedureResponse]:
    try:
        items = await service.list_procedures(doctor.doctor_id, patient_id)
    except ProcedurePatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [ProcedureResponse.model_validate(item) for item in items]


@router.post("/patients/{patient_id}/procedures", response_model=ProcedureResponse, status_code=status.HTTP_201_CREATED)
async def create_procedure(
    patient_id: UUID,
    payload: ProcedureCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ProcedureService = Depends(get_procedure_service),
) -> ProcedureResponse:
    try:
        item = await service.create_procedure(
            doctor.doctor_id,
            patient_id,
            CreateProcedureInput(**payload.model_dump()),
        )
    except ProcedurePatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProcedureValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ProcedureResponse.model_validate(item)


@router.get("/procedures/{procedure_id}", response_model=ProcedureResponse)
async def get_procedure(
    procedure_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ProcedureService = Depends(get_procedure_service),
) -> ProcedureResponse:
    try:
        item = await service.get_procedure(doctor.doctor_id, procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProcedureResponse.model_validate(item)


@router.put("/procedures/{procedure_id}", response_model=ProcedureResponse)
async def update_procedure(
    procedure_id: UUID,
    payload: ProcedureUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ProcedureService = Depends(get_procedure_service),
) -> ProcedureResponse:
    try:
        item = await service.update_procedure(
            doctor.doctor_id,
            procedure_id,
            UpdateProcedureInput(**payload.model_dump()),
        )
    except ProcedureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProcedureValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ProcedureResponse.model_validate(item)


@router.delete("/procedures/{procedure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_procedure(
    procedure_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ProcedureService = Depends(get_procedure_service),
) -> Response:
    try:
        await service.delete_procedure(doctor.doctor_id, procedure_id)
    except ProcedureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
