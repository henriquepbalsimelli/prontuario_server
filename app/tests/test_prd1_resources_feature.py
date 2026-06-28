from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.application.services.continuous_medication_service import (
    ContinuousMedicationService,
    CreateContinuousMedicationInput,
    ContinuousMedicationValidationError,
    UpdateContinuousMedicationInput,
)
from app.application.services.doctor_template_service import (
    CreateDoctorTemplateInput,
    DoctorTemplateService,
)
from app.application.services.exam_service import CreateExamInput, ExamService, ExamValidationError
from app.application.services.medical_history_service import (
    CreateMedicalHistoryInput,
    MedicalHistoryService,
    MedicalHistoryValidationError,
)
from app.application.services.text_document_service import (
    CreateTextDocumentFromTemplateInput,
    TextDocumentService,
    UpdateTextDocumentInput,
)
from app.application.services.timeline_service import TimelineService
from app.domain.models.consultation import Consultation
from app.domain.models.continuous_medication import ContinuousMedication
from app.domain.models.doctor_template import DoctorTemplate
from app.domain.models.exam import EXAM_STATUS_REQUESTED, Exam
from app.domain.models.medical_history import MedicalHistory
from app.domain.models.procedure import Procedure
from app.domain.models.text_document import TextDocument
from app.domain.models.timeline import TimelineEvent
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import (
    get_continuous_medication_service,
    get_doctor_template_service,
    get_exam_service,
    get_medical_history_service,
    get_procedure_service,
    get_text_document_service,
    get_timeline_service,
)
from app.presentation.main import create_app


def test_continuous_medication_service_crud_and_audit() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    medication_id = uuid4()
    repository = AsyncMock()
    repository.create.side_effect = lambda item: item
    repository.get_by_id.return_value = ContinuousMedication(
        id=medication_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        name="Losartana",
        status="active",
    )
    repository.update.side_effect = lambda item: item
    repository.delete.return_value = True
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    consultation_repository = AsyncMock()
    audit = AsyncMock()
    service = ContinuousMedicationService(repository, patient_repository, consultation_repository, audit)

    created = asyncio.run(
        service.create_medication(
            doctor_id,
            patient_id,
            CreateContinuousMedicationInput(name="Losartana", status="active"),
        )
    )
    updated = asyncio.run(
        service.update_medication(
            doctor_id,
            medication_id,
            UpdateContinuousMedicationInput(name="Losartana", status="inactive"),
        )
    )
    asyncio.run(service.delete_medication(doctor_id, medication_id))

    assert created.name == "Losartana"
    assert updated.status == "inactive"
    assert audit.record_write.await_count == 3
    consultation_repository.get_by_id.assert_not_awaited()


def test_exam_service_validates_consultation_reference() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = None
    service = ExamService(repository, patient_repository, consultation_repository)

    try:
        asyncio.run(
            service.create_exam(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateExamInput(
                    name="Hemograma",
                    status=EXAM_STATUS_REQUESTED,
                    consultation_id=uuid4(),
                ),
            )
        )
    except ExamValidationError as exc:
        assert str(exc) == "Consultation not found for patient"
    else:
        raise AssertionError("Expected invalid consultation reference to fail")


def test_continuous_medication_service_validates_consultation_reference() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = None
    service = ContinuousMedicationService(repository, patient_repository, consultation_repository)

    try:
        asyncio.run(
            service.create_medication(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateContinuousMedicationInput(
                    name="Losartana",
                    status="active",
                    consultation_id=uuid4(),
                ),
            )
        )
    except ContinuousMedicationValidationError as exc:
        assert str(exc) == "Consultation not found for patient"
    else:
        raise AssertionError("Expected invalid consultation reference to fail")


def test_medical_history_service_validates_consultation_reference() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = None
    service = MedicalHistoryService(repository, patient_repository, consultation_repository)

    try:
        asyncio.run(
            service.create_history(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateMedicalHistoryInput(
                    body="Asma na infância",
                    consultation_id=uuid4(),
                ),
            )
        )
    except MedicalHistoryValidationError as exc:
        assert str(exc) == "Consultation not found for patient"
    else:
        raise AssertionError("Expected invalid consultation reference to fail")


def test_timeline_service_aggregates_consultations_and_procedures() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    procedure_id = uuid4()
    consultation_repository = AsyncMock()
    consultation_repository.list_by_patient.return_value = [
        Consultation(
            id=consultation_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_date=date(2026, 6, 10),
            diagnosis="Rosacea",
        )
    ]
    procedure_repository = AsyncMock()
    procedure_repository.list_by_patient.return_value = [
        Procedure(
            id=procedure_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            procedure_date=date(2026, 6, 11),
            title="Laser",
            description="Sessao",
        )
    ]
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = TimelineService(consultation_repository, procedure_repository, patient_repository)

    events = asyncio.run(service.list_timeline(doctor_id, patient_id, ["consultation", "procedure"]))

    assert [event.source_type for event in events] == ["procedure", "consultation"]
    assert events[0].title == "Laser"
    assert events[1].title == "Evolucao clinica/consulta"


def test_template_and_document_services_create_and_version_documents() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    document_id = uuid4()
    template = DoctorTemplate(
        id=uuid4(),
        doctor_id=doctor_id,
        title="Receita base",
        type="prescription",
        body="Texto base",
    )
    template_repository = AsyncMock()
    template_repository.create.side_effect = lambda item: item
    template_repository.get_by_id.return_value = template
    template_service = DoctorTemplateService(template_repository)

    created_template = asyncio.run(
        template_service.create_template(
            doctor_id,
            CreateDoctorTemplateInput(title="Receita base", type="prescription", body="Texto base"),
        )
    )

    document_repository = AsyncMock()
    document_repository.create.side_effect = lambda item: item
    document_repository.get_by_id.return_value = TextDocument(
        id=document_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        template_id=template.id,
        type="prescription",
        title="Receita base",
        body="Texto base",
        version=1,
    )
    document_repository.update.side_effect = lambda item: item
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    consultation_repository = AsyncMock()
    document_service = TextDocumentService(
        document_repository,
        patient_repository,
        consultation_repository,
        template_repository,
    )

    created_document = asyncio.run(
        document_service.create_from_template(
            doctor_id,
            patient_id,
            CreateTextDocumentFromTemplateInput(template_id=template.id),
        )
    )
    updated_document = asyncio.run(
        document_service.update_document(
            doctor_id,
            document_id,
            UpdateTextDocumentInput(
                type="prescription",
                title="Receita final",
                body="Texto final",
            ),
        )
    )

    assert created_template.type == "prescription"
    assert created_document.version == 1
    assert updated_document.version == 2


def test_backend_prd1_routes_are_exposed_in_openapi() -> None:
    app = create_app()
    try:
        schema = app.openapi()
    finally:
        asyncio.run(app.state.container.close())

    expected_paths = {
        "/patients/{patient_id}/continuous-medications",
        "/continuous-medications/{medication_id}",
        "/patients/{patient_id}/medical-histories",
        "/medical-histories/{history_id}",
        "/patients/{patient_id}/exams",
        "/exams/{exam_id}",
        "/patients/{patient_id}/procedures",
        "/procedures/{procedure_id}",
        "/patients/{patient_id}/timeline",
        "/doctor/templates",
        "/doctor/templates/{template_id}",
        "/patients/{patient_id}/text-documents",
        "/patients/{patient_id}/text-documents/from-template",
        "/text-documents/{document_id}",
    }
    assert expected_paths.issubset(schema["paths"].keys())


def test_backend_prd1_endpoints_contracts() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    medication_id = uuid4()
    history_id = uuid4()
    exam_id = uuid4()
    procedure_id = uuid4()
    template_id = uuid4()
    document_id = uuid4()
    continuous_medication_service = AsyncMock()
    continuous_medication_service.list_medications.return_value = [
        ContinuousMedication(
            id=medication_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            name="Metformina",
            status="active",
        )
    ]
    continuous_medication_service.create_medication.return_value = (
        continuous_medication_service.list_medications.return_value[0]
    )

    medical_history_service = AsyncMock()
    medical_history_service.list_histories.return_value = [
        MedicalHistory(
            id=history_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            body="Asma",
        )
    ]
    medical_history_service.create_history.return_value = (
        medical_history_service.list_histories.return_value[0]
    )
    medical_history_service.update_history.return_value = (
        medical_history_service.list_histories.return_value[0]
    )

    exam_service = AsyncMock()
    exam_service.list_exams.return_value = [
        Exam(
            id=exam_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            name="Hemograma",
            status="requested",
        )
    ]
    exam_service.create_exam.return_value = exam_service.list_exams.return_value[0]

    procedure_service = AsyncMock()
    procedure_service.list_procedures.return_value = [
        Procedure(
            id=procedure_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            title="Peeling",
        )
    ]
    procedure_service.create_procedure.return_value = procedure_service.list_procedures.return_value[0]

    timeline_service = AsyncMock()
    timeline_service.list_timeline.return_value = [
        TimelineEvent(
            id=f"consultation:{procedure_id}",
            source_type="consultation",
            occurred_at=date(2026, 6, 12),
            title="Evolucao clinica/consulta",
            summary="Rosacea",
            consultation_id=procedure_id,
            source_id=procedure_id,
        )
    ]

    template_service = AsyncMock()
    template_service.list_templates.return_value = [
        DoctorTemplate(
            id=template_id,
            doctor_id=doctor_id,
            title="Modelo",
            type="conduct",
            body="Texto",
        )
    ]
    template_service.create_template.return_value = template_service.list_templates.return_value[0]

    document_service = AsyncMock()
    document_service.list_documents.return_value = [
        TextDocument(
            id=document_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            template_id=template_id,
            type="prescription",
            title="Doc",
            body="Texto",
            version=1,
        )
    ]
    document_service.create_from_template.return_value = document_service.list_documents.return_value[0]

    app = create_app()
    app.dependency_overrides[get_authenticated_doctor] = lambda: AuthenticatedDoctor(doctor_id=doctor_id)
    app.dependency_overrides[get_continuous_medication_service] = lambda: continuous_medication_service
    app.dependency_overrides[get_medical_history_service] = lambda: medical_history_service
    app.dependency_overrides[get_exam_service] = lambda: exam_service
    app.dependency_overrides[get_procedure_service] = lambda: procedure_service
    app.dependency_overrides[get_timeline_service] = lambda: timeline_service
    app.dependency_overrides[get_doctor_template_service] = lambda: template_service
    app.dependency_overrides[get_text_document_service] = lambda: document_service

    with TestClient(app) as client:
        assert client.get(f"/patients/{patient_id}/continuous-medications").status_code == 200
        assert client.post(
            f"/patients/{patient_id}/continuous-medications",
            json={"name": "Metformina", "status": "active"},
        ).status_code == 201
        assert client.get(f"/patients/{patient_id}/medical-histories").status_code == 200
        assert client.post(
            f"/patients/{patient_id}/medical-histories",
            json={"body": "Asma"},
        ).status_code == 201
        assert client.put(
            f"/medical-histories/{history_id}",
            json={"body": "Asma"},
        ).status_code == 200
        assert client.delete(f"/medical-histories/{history_id}").status_code == 204
        assert client.get(f"/patients/{patient_id}/exams").status_code == 200
        assert client.post(
            f"/patients/{patient_id}/exams",
            json={"name": "Hemograma", "status": "requested"},
        ).status_code == 201
        assert client.get(f"/patients/{patient_id}/procedures").status_code == 200
        assert client.post(
            f"/patients/{patient_id}/procedures",
            json={"title": "Peeling"},
        ).status_code == 201
        timeline_response = client.get(
            f"/patients/{patient_id}/timeline?types=consultation&types=procedure"
        )
        assert timeline_response.status_code == 200
        assert timeline_response.json()[0]["source_type"] == "consultation"
        assert client.get("/doctor/templates").status_code == 200
        assert client.post(
            "/doctor/templates",
            json={"title": "Modelo", "type": "conduct", "body": "Texto"},
        ).status_code == 201
        assert client.get(f"/patients/{patient_id}/text-documents").status_code == 200
        assert client.post(
            f"/patients/{patient_id}/text-documents/from-template",
            json={"template_id": str(template_id)},
        ).status_code == 201

    app.dependency_overrides.clear()
