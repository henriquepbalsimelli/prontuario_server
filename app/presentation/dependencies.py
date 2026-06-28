from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.container import Container
from app.application.services.auth_service import AuthService
from app.application.services.audit_event_service import AuditEventService
from app.application.services.consultation_service import ConsultationService
from app.application.services.continuous_medication_service import ContinuousMedicationService
from app.application.services.doctor_template_service import DoctorTemplateService
from app.application.services.disease_service import DiseaseService
from app.application.services.exam_service import ExamService
from app.application.services.doctor_service import DoctorService
from app.application.services.evolution_service import EvolutionService
from app.application.services.health_service import HealthService
from app.application.services.image_service import ImageService
from app.application.services.lesion_service import LesionService
from app.application.services.medication_service import MedicationService
from app.application.services.medical_history_service import MedicalHistoryService
from app.application.services.patient_service import PatientService
from app.application.services.procedure_service import ProcedureService
from app.application.services.text_document_service import TextDocumentService
from app.application.services.timeline_service import TimelineService
from app.infrastructure.repositories.sqlalchemy_continuous_medication_repository import (
    SQLAlchemyContinuousMedicationRepository,
)
from app.infrastructure.repositories.sqlalchemy_consultation_repository import (
    SQLAlchemyConsultationRepository,
)
from app.infrastructure.repositories.sqlalchemy_disease_repository import SQLAlchemyDiseaseRepository
from app.infrastructure.repositories.sqlalchemy_doctor_template_repository import (
    SQLAlchemyDoctorTemplateRepository,
)
from app.infrastructure.repositories.sqlalchemy_doctor_repository import SQLAlchemyDoctorRepository
from app.infrastructure.repositories.sqlalchemy_evolution_repository import SQLAlchemyEvolutionRepository
from app.infrastructure.repositories.sqlalchemy_exam_repository import SQLAlchemyExamRepository
from app.infrastructure.repositories.sqlalchemy_image_repository import SQLAlchemyImageRepository
from app.infrastructure.repositories.sqlalchemy_lesion_repository import SQLAlchemyLesionRepository
from app.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.infrastructure.repositories.sqlalchemy_medical_history_repository import (
    SQLAlchemyMedicalHistoryRepository,
)
from app.infrastructure.repositories.sqlalchemy_patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.repositories.sqlalchemy_procedure_repository import SQLAlchemyProcedureRepository
from app.infrastructure.repositories.sqlalchemy_text_document_repository import (
    SQLAlchemyTextDocumentRepository,
)
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
    medical_history_repository = SQLAlchemyMedicalHistoryRepository(session=session)
    continuous_medication_repository = SQLAlchemyContinuousMedicationRepository(session=session)
    evolution_repository = SQLAlchemyEvolutionRepository(session=session)
    return ConsultationService(
        consultation_repository=consultation_repository,
        patient_repository=patient_repository,
        medical_history_repository=medical_history_repository,
        continuous_medication_repository=continuous_medication_repository,
        evolution_repository=evolution_repository,
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


def get_evolution_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> EvolutionService:
    repository = SQLAlchemyEvolutionRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    return EvolutionService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )


def get_continuous_medication_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> ContinuousMedicationService:
    repository = SQLAlchemyContinuousMedicationRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    return ContinuousMedicationService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )


def get_medical_history_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> MedicalHistoryService:
    repository = SQLAlchemyMedicalHistoryRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    return MedicalHistoryService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )


def get_exam_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> ExamService:
    repository = SQLAlchemyExamRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    return ExamService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )


def get_procedure_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> ProcedureService:
    repository = SQLAlchemyProcedureRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    return ProcedureService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )


def get_timeline_service(
    session: AsyncSession = Depends(get_db_session),
) -> TimelineService:
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    procedure_repository = SQLAlchemyProcedureRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    return TimelineService(
        consultation_repository=consultation_repository,
        procedure_repository=procedure_repository,
        patient_repository=patient_repository,
    )


def get_doctor_template_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> DoctorTemplateService:
    repository = SQLAlchemyDoctorTemplateRepository(session=session)
    return DoctorTemplateService(repository=repository, audit_event_service=audit_event_service)


def get_text_document_service(
    session: AsyncSession = Depends(get_db_session),
    audit_event_service: AuditEventService = Depends(get_audit_event_service),
) -> TextDocumentService:
    repository = SQLAlchemyTextDocumentRepository(session=session)
    patient_repository = SQLAlchemyPatientRepository(session=session)
    consultation_repository = SQLAlchemyConsultationRepository(session=session)
    template_repository = SQLAlchemyDoctorTemplateRepository(session=session)
    return TextDocumentService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        template_repository=template_repository,
        audit_event_service=audit_event_service,
    )
