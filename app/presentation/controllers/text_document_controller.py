from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.services.text_document_service import (
    CreateTextDocumentFromTemplateInput,
    TextDocumentNotFoundError,
    TextDocumentPatientNotFoundError,
    TextDocumentService,
    TextDocumentValidationError,
    UpdateTextDocumentInput,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_text_document_service
from app.presentation.schemas.text_document_schema import (
    TextDocumentCreateFromTemplateRequest,
    TextDocumentResponse,
    TextDocumentUpdateRequest,
)

router = APIRouter(tags=["text_documents"])


@router.get("/patients/{patient_id}/text-documents", response_model=list[TextDocumentResponse])
async def list_text_documents(
    patient_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TextDocumentService = Depends(get_text_document_service),
) -> list[TextDocumentResponse]:
    try:
        items = await service.list_documents(doctor.doctor_id, patient_id)
    except TextDocumentPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [TextDocumentResponse.model_validate(item) for item in items]


@router.post("/patients/{patient_id}/text-documents/from-template", response_model=TextDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_text_document_from_template(
    patient_id: UUID,
    payload: TextDocumentCreateFromTemplateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TextDocumentService = Depends(get_text_document_service),
) -> TextDocumentResponse:
    try:
        item = await service.create_from_template(
            doctor.doctor_id,
            patient_id,
            CreateTextDocumentFromTemplateInput(**payload.model_dump()),
        )
    except TextDocumentPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TextDocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return TextDocumentResponse.model_validate(item)


@router.get("/text-documents/{document_id}", response_model=TextDocumentResponse)
async def get_text_document(
    document_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TextDocumentService = Depends(get_text_document_service),
) -> TextDocumentResponse:
    try:
        item = await service.get_document(doctor.doctor_id, document_id)
    except TextDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TextDocumentResponse.model_validate(item)


@router.put("/text-documents/{document_id}", response_model=TextDocumentResponse)
async def update_text_document(
    document_id: UUID,
    payload: TextDocumentUpdateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TextDocumentService = Depends(get_text_document_service),
) -> TextDocumentResponse:
    try:
        item = await service.update_document(
            doctor.doctor_id,
            document_id,
            UpdateTextDocumentInput(**payload.model_dump()),
        )
    except TextDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TextDocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return TextDocumentResponse.model_validate(item)


@router.delete("/text-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_text_document(
    document_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TextDocumentService = Depends(get_text_document_service),
) -> Response:
    try:
        await service.delete_document(doctor.doctor_id, document_id)
    except TextDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
