from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.services.patient_service import (
    CreatePatientInput,
    PatientNotFoundError,
    PatientService,
    UpdatePatientInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_patient_service
from app.presentation.schemas.patient_schema import (
    PatientCreateRequest,
    PatientResponse,
    PatientUpdateRequest,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: PatientService = Depends(get_patient_service),
) -> list[PatientResponse]:
    patients = await service.list_patients(
        doctor_id=doctor.doctor_id,
        page=page,
        page_size=page_size,
    )
    return [PatientResponse.model_validate(patient) for patient in patients]


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    patient = await service.create_patient(
        doctor_id=doctor.doctor_id,
        payload=CreatePatientInput(**payload.model_dump()),
    )
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    try:
        patient = await service.get_patient(doctor_id=doctor.doctor_id, patient_id=patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PatientResponse.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    payload: PatientUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    try:
        patient = await service.update_patient(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            payload=UpdatePatientInput(**payload.model_dump()),
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    try:
        await service.delete_patient(doctor_id=doctor.doctor_id, patient_id=patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
