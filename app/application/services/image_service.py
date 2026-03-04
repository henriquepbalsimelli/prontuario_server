from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.audit_utils import to_audit_dict
from app.domain.interfaces.image_repository import ImageRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.models.image import Image
from app.infrastructure.s3.object_inspector import S3ObjectInspector
from app.infrastructure.s3.presigner import S3Presigner


class ImagePatientNotFoundError(Exception):
    pass


class ImageNotFoundError(Exception):
    pass


class ImageUploadNotFoundInS3Error(Exception):
    pass


@dataclass(slots=True)
class CreateImageUploadInput:
    patient_id: UUID
    consultation_id: UUID | None
    file_name: str
    content_type: str
    image_type: str | None = None
    body_region: str | None = None
    coord_x: float | None = None
    coord_y: float | None = None


@dataclass(slots=True)
class PresignedUploadResult:
    image: Image
    upload_url: str
    expires_in: int
    max_upload_size_mb: int


class ImageService:
    def __init__(
        self,
        image_repository: ImageRepository,
        patient_repository: PatientRepository,
        presigner: S3Presigner,
        object_inspector: S3ObjectInspector,
        s3_bucket_name: str,
        presigned_expires_seconds: int,
        max_upload_size_mb: int,
        audit_event_service: AuditEventService | None = None,
    ) -> None:
        self.image_repository = image_repository
        self.patient_repository = patient_repository
        self.presigner = presigner
        self.object_inspector = object_inspector
        self.s3_bucket_name = s3_bucket_name
        self.presigned_expires_seconds = presigned_expires_seconds
        self.max_upload_size_mb = max_upload_size_mb
        self.audit_event_service = audit_event_service

    async def list_images(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int,
        page_size: int,
    ) -> list[Image]:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if patient is None:
            raise ImagePatientNotFoundError("Patient not found")

        return await self.image_repository.list_by_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size,
        )

    async def create_presigned_upload(
        self,
        doctor_id: UUID,
        payload: CreateImageUploadInput,
    ) -> PresignedUploadResult:
        patient = await self.patient_repository.get_by_id(
            doctor_id=doctor_id,
            patient_id=payload.patient_id,
        )
        if patient is None:
            raise ImagePatientNotFoundError("Patient not found")

        suffix = Path(payload.file_name).suffix.lower()
        object_name = f"{uuid4()}{suffix}" if suffix else str(uuid4())
        s3_key = f"doctors/{doctor_id}/patients/{payload.patient_id}/{object_name}"

        image = Image(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=payload.patient_id,
            consultation_id=payload.consultation_id,
            s3_key=s3_key,
            type=payload.image_type or payload.content_type,
            body_region=payload.body_region,
            coord_x=payload.coord_x,
            coord_y=payload.coord_y,
        )

        saved = await self.image_repository.create(image=image)
        upload_url = self.presigner.generate_put_url(
            bucket=self.s3_bucket_name,
            key=s3_key,
            content_type=payload.content_type,
            expires_seconds=self.presigned_expires_seconds,
        )

        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="image",
                entity_id=saved.id,
                action="create",
                event_type="ImageUploadRequested",
                before_state=None,
                after_state=to_audit_dict(saved),
            )

        return PresignedUploadResult(
            image=saved,
            upload_url=upload_url,
            expires_in=self.presigned_expires_seconds,
            max_upload_size_mb=self.max_upload_size_mb,
        )

    async def confirm_upload(self, doctor_id: UUID, image_id: UUID) -> Image:
        image = await self.image_repository.get_by_id(doctor_id=doctor_id, image_id=image_id)
        if image is None:
            raise ImageNotFoundError("Image not found")

        metadata = self.object_inspector.head_object(
            bucket=self.s3_bucket_name,
            key=image.s3_key,
        )
        if not metadata.exists:
            raise ImageUploadNotFoundInS3Error("Uploaded file not found in S3")

        updated = await self.image_repository.mark_uploaded(
            doctor_id=doctor_id,
            image_id=image_id,
            file_size_bytes=metadata.size_bytes,
            etag=metadata.etag,
        )
        if updated is None:
            raise ImageNotFoundError("Image not found")

        if self.audit_event_service is not None:
            await self.audit_event_service.record_write(
                doctor_id=doctor_id,
                entity_type="image",
                entity_id=updated.id,
                action="update",
                event_type="ImageUploaded",
                before_state=to_audit_dict(image),
                after_state=to_audit_dict(updated),
            )

        return updated
