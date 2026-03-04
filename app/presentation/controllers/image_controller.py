from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.image_service import (
    CreateImageUploadInput,
    ImageNotFoundError,
    ImagePatientNotFoundError,
    ImageService,
    ImageUploadNotFoundInS3Error,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_image_service
from app.presentation.schemas.image_schema import (
    ImageConfirmUploadResponse,
    ImagePresignedUrlRequest,
    ImagePresignedUrlResponse,
    ImageResponse,
)

router = APIRouter(tags=["images"])


@router.post("/images/presigned-url", response_model=ImagePresignedUrlResponse)
async def create_presigned_url(
    payload: ImagePresignedUrlRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ImageService = Depends(get_image_service),
) -> ImagePresignedUrlResponse:
    try:
        result = await service.create_presigned_upload(
            doctor_id=doctor.doctor_id,
            payload=CreateImageUploadInput(**payload.model_dump()),
        )
    except ImagePatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ImagePresignedUrlResponse(
        image=ImageResponse.model_validate(result.image),
        upload_url=result.upload_url,
        method="PUT",
        expires_in=result.expires_in,
        max_upload_size_mb=result.max_upload_size_mb,
    )


@router.get("/patients/{patient_id}/images", response_model=list[ImageResponse])
async def list_patient_images(
    patient_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ImageService = Depends(get_image_service),
) -> list[ImageResponse]:
    try:
        images = await service.list_images(
            doctor_id=doctor.doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )
    except ImagePatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ImageResponse.model_validate(item) for item in images]


@router.post("/images/{image_id}/confirm-upload", response_model=ImageConfirmUploadResponse)
async def confirm_image_upload(
    image_id: UUID,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: ImageService = Depends(get_image_service),
) -> ImageConfirmUploadResponse:
    try:
        image = await service.confirm_upload(doctor_id=doctor.doctor_id, image_id=image_id)
    except ImageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ImageUploadNotFoundInS3Error as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ImageConfirmUploadResponse(image=ImageResponse.model_validate(image))
