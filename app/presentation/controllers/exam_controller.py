from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.services.exam_service import (
    CreateExamInput,
    ExamNotFoundError,
    ExamPatientNotFoundError,
    ExamService,
    ExamValidationError,
    UpdateExamInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_exam_service
from app.presentation.schemas.exam_schema import ExamCreateRequest, ExamResponse, ExamUpdateRequest

router = APIRouter(tags=["exams"])


@router.get("/patients/{patient_id}/exams", response_model=list[ExamResponse])
async def list_exams(
    patient_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    consultation_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ExamService = Depends(get_exam_service),
) -> list[ExamResponse]:
    try:
        items = await service.list_exams(
            doctor.doctor_id,
            patient_id,
            status_filter,
            consultation_id,
            start_date,
            end_date,
        )
    except ExamPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExamValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [ExamResponse.model_validate(item) for item in items]


@router.post("/patients/{patient_id}/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    patient_id: UUID,
    payload: ExamCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ExamService = Depends(get_exam_service),
) -> ExamResponse:
    try:
        item = await service.create_exam(doctor.doctor_id, patient_id, CreateExamInput(**payload.model_dump()))
    except ExamPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExamValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ExamResponse.model_validate(item)


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ExamService = Depends(get_exam_service),
) -> ExamResponse:
    try:
        item = await service.get_exam(doctor.doctor_id, exam_id)
    except ExamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExamResponse.model_validate(item)


@router.put("/exams/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    payload: ExamUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ExamService = Depends(get_exam_service),
) -> ExamResponse:
    try:
        item = await service.update_exam(doctor.doctor_id, exam_id, UpdateExamInput(**payload.model_dump()))
    except ExamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExamValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ExamResponse.model_validate(item)


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ExamService = Depends(get_exam_service),
) -> Response:
    try:
        await service.delete_exam(doctor.doctor_id, exam_id)
    except ExamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
