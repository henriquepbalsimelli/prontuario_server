from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.container import Container
from app.application.services.auth_service import AuthService
from app.application.services.audit_event_service import AuditEventService
from app.application.services.consultation_service import ConsultationService
from app.application.services.disease_service import DiseaseService
from app.application.services.doctor_service import DoctorService
from app.application.services.health_service import HealthService
from app.application.services.image_service import ImageService
from app.application.services.lesion_service import LesionService
from app.application.services.medication_service import MedicationService
from app.application.services.patient_service import PatientService
from app.infrastructure.repositories.sqlalchemy_consultation_repository import (
    SQLAlchemyConsultationRepository,
)
from app.infrastructure.repositories.sqlalchemy_disease_repository import SQLAlchemyDiseaseRepository
from app.infrastructure.repositories.sqlalchemy_doctor_repository import SQLAlchemyDoctorRepository
from app.infrastructure.repositories.sqlalchemy_image_repository import SQLAlchemyImageRepository
from app.infrastructure.repositories.sqlalchemy_lesion_repository import SQLAlchemyLesionRepository
from app.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.infrastructure.repositories.sqlalchemy_patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.s3.object_inspector import S3ObjectInspector
from app.infrastructure.s3.presigner import S3Presigner
from app.infrastructure.event_bus import SQLAlchemyDomainEventBus


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_health_service(container: Container = Depends(get_container)) -> HealthService:
    return container.health_service()


async def get_db_session(
    container: Container = Depends(get_container),
) -> AsyncIterator[AsyncSession]:
    async for session in container.db_session():
        yield session


def get_audit_event_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuditEventService:
    event_bus = SQLAlchemyDomainEventBus(session=session)
    return AuditEventService(session=session, event_bus=event_bus)


def get_patient_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> PatientService:
    repository = SQLAlchemyPatientRepository(session=session)
    return PatientService(repository=repository, audit_event_service=audit_event_service)


def get_doctor_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> DoctorService:
    repository = SQLAlchemyDoctorRepository(session=session)
    return DoctorService(repository=repository, audit_event_service=audit_event_service)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> AuthService:
    repository = SQLAlchemyDoctorRepository(session=session)
    return AuthService(
        repository=repository,
        jwt_secret_key=container.settings.jwt_secret_key,
        jwt_algorithm=container.settings.jwt_algorithm,
        jwt_access_token_exp_minutes=container.settings.jwt_access_token_exp_minutes,
    )


def get_consultation_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> ConsultationService:
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    return ConsultationService(
        consultation_repository=consultation_repository,
        patient_repository=patient_repository,
        audit_event_service=audit_event_service,
    )


def get_disease_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> DiseaseService:
    repository = SQLAlchemyDiseaseRepository(session=session)
    return DiseaseService(repository=repository, audit_event_service=audit_event_service)


def get_medication_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> MedicationService:
    repository = SQLAlchemyMedicationRepository(session=session)
    return MedicationService(repository=repository, audit_event_service=audit_event_service)


def get_image_service(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> ImageService:
    image_repository = SQLAlchemyImageRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    presigner = S3Presigner(region=container.settings.s3_region)
    object_inspector = S3ObjectInspector(region=container.settings.s3_region)
    return ImageService(
        image_repository=image_repository,
        patient_repository=patient_repository,
        presigner=presigner,
        object_inspector=object_inspector,
        s3_bucket_name=container.settings.s3_bucket_name,
        presigned_expires_seconds=container.settings.s3_presigned_expires_seconds,
        max_upload_size_mb=container.settings.max_upload_size_mb,
        audit_event_service=audit_event_service,
    )


def get_lesion_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> LesionService:
    lesion_repository = SQLAlchemyLesionRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    return LesionService(
        lesion_repository=lesion_repository,
        patient_repository=patient_repository,
        audit_event_service=audit_event_service,
    )
