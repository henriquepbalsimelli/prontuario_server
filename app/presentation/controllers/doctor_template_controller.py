from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.services.doctor_template_service import (
    CreateDoctorTemplateInput,
    DoctorTemplateNotFoundError,
    DoctorTemplateService,
    DoctorTemplateValidationError,
    UpdateDoctorTemplateInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_doctor_template_service
from app.presentation.schemas.doctor_template_schema import (
    DoctorTemplateCreateRequest,
    DoctorTemplateResponse,
    DoctorTemplateUpdateRequest,
)

router = APIRouter(prefix="/doctor/templates", tags=["doctor_templates"])


@router.get("", response_model=list[DoctorTemplateResponse])
async def list_doctor_templates(
    type_filter: str | None = Query(default=None, alias="type"),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DoctorTemplateService = Depends(get_doctor_template_service),
) -> list[DoctorTemplateResponse]:
    try:
        items = await service.list_templates(doctor.doctor_id, type_filter)
    except DoctorTemplateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [DoctorTemplateResponse.model_validate(item) for item in items]


@router.post("", response_model=DoctorTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_template(
    payload: DoctorTemplateCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DoctorTemplateService = Depends(get_doctor_template_service),
) -> DoctorTemplateResponse:
    try:
        item = await service.create_template(doctor.doctor_id, CreateDoctorTemplateInput(**payload.model_dump()))
    except DoctorTemplateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DoctorTemplateResponse.model_validate(item)


@router.get("/{template_id}", response_model=DoctorTemplateResponse)
async def get_doctor_template(
    template_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DoctorTemplateService = Depends(get_doctor_template_service),
) -> DoctorTemplateResponse:
    try:
        item = await service.get_template(doctor.doctor_id, template_id)
    except DoctorTemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DoctorTemplateResponse.model_validate(item)


@router.put("/{template_id}", response_model=DoctorTemplateResponse)
async def update_doctor_template(
    template_id: UUID,
    payload: DoctorTemplateUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DoctorTemplateService = Depends(get_doctor_template_service),
) -> DoctorTemplateResponse:
    try:
        item = await service.update_template(doctor.doctor_id, template_id, UpdateDoctorTemplateInput(**payload.model_dump()))
    except DoctorTemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DoctorTemplateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DoctorTemplateResponse.model_validate(item)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor_template(
    template_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DoctorTemplateService = Depends(get_doctor_template_service),
) -> Response:
    try:
        await service.delete_template(doctor.doctor_id, template_id)
    except DoctorTemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
