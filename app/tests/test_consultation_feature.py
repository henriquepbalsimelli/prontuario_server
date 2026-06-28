from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.application.services.consultation_service import (
    ConsultationMedicationInput,
    ConsultationCopySourceNotFoundError,
    ConsultationNotFoundError,
    ConsultationPatientNotFoundError,
    ConsultationScheduleConflictError,
    ConsultationService,
    ConsultationValidationError,
    CreateConsultationInput,
    UpdateConsultationInput,
)
from app.domain.models.consultation import (
    CONSULTATION_STATUS_CANCELLED,
    CONSULTATION_STATUS_COMPLETED,
    CONSULTATION_STATUS_SCHEDULED,
    Consultation,
)
from app.domain.models.continuous_medication import ContinuousMedication
from app.domain.models.evolution import Evolution
from app.domain.models.medical_history import MedicalHistory
from app.infrastructure.repositories.sqlalchemy_consultation_repository import (
    SQLAlchemyConsultationRepository,
)
from app.infrastructure.repositories.sqlalchemy_evolution_repository import (
    SQLAlchemyEvolutionRepository,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_consultation_service
from app.presentation.main import create_app
from app.presentation.schemas.consultation_schema import ConsultationCreateRequest


class _ScalarResult:
    def __init__(self, rows: list[object] | None = None, row: object = None) -> None:
        self._rows = rows or []
        self._row = row

    def all(self) -> list[object]:
        return self._rows


class _ExecuteResult:
    def __init__(self, rows: list[object] | None = None, row: object = None) -> None:
        self._rows = rows or []
        self._row = row

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(rows=self._rows)

    def scalar_one_or_none(self) -> object:
        return self._row

    def scalar_one(self) -> object:
        return self._row


def test_consultation_service_get_returns_404_for_inaccessible_consultation() -> None:
    repository = AsyncMock()
    repository.get_by_id.return_value = None
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=AsyncMock(),
    )

    try:
        asyncio.run(service.get_consultation(doctor_id=uuid4(), consultation_id=uuid4()))
    except ConsultationNotFoundError as exc:
        assert str(exc) == "Consultation not found"
    else:
        raise AssertionError("Expected inaccessible consultation to raise not found")


def test_consultation_service_update_preserves_identity_and_audits() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    created_at = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    scheduled_start_at = datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc)
    scheduled_end_at = datetime(2026, 6, 2, 9, 30, tzinfo=timezone.utc)
    existing = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 2),
        scheduled_start_at=scheduled_start_at,
        scheduled_end_at=scheduled_end_at,
        status=CONSULTATION_STATUS_SCHEDULED,
        diagnosis="Antes",
        notes="Observacao antes",
        chief_complaint="Antes",
        physical_exam="Exame antes",
        conduct="Conduta antes",
        created_at=created_at,
    )
    updated_start_at = datetime(2026, 6, 4, 11, 0, tzinfo=timezone.utc)
    updated = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 4),
        scheduled_start_at=updated_start_at,
        scheduled_end_at=updated_start_at + timedelta(minutes=30),
        status=CONSULTATION_STATUS_COMPLETED,
        diagnosis="Depois",
        notes="Observacao depois",
        chief_complaint="Depois",
        physical_exam="Exame depois",
        conduct="Conduta depois",
        created_at=created_at,
    )
    repository = AsyncMock()
    repository.get_by_id.return_value = existing
    repository.has_schedule_overlap.return_value = False
    repository.update.return_value = updated
    audit_event_service = AsyncMock()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=AsyncMock(),
        evolution_repository=AsyncMock(),
        audit_event_service=audit_event_service,
    )

    result = asyncio.run(
        service.update_consultation(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            payload=UpdateConsultationInput(
                fields={
                    "scheduled_start_at": updated_start_at,
                    "status": CONSULTATION_STATUS_COMPLETED,
                    "diagnosis": "Depois",
                    "notes": "Observacao depois",
                    "chief_complaint": "Depois",
                    "physical_exam": "Exame depois",
                    "conduct": "Conduta depois",
                }
            ),
        )
    )

    assert result == updated
    saved = repository.update.await_args.kwargs["consultation"]
    assert saved.id == consultation_id
    assert saved.doctor_id == doctor_id
    assert saved.patient_id == patient_id
    assert saved.created_at == created_at
    assert saved.consultation_date == date(2026, 6, 4)
    assert saved.scheduled_end_at == updated_start_at + timedelta(minutes=30)
    assert saved.status == CONSULTATION_STATUS_COMPLETED
    assert saved.diagnosis == "Depois"
    assert saved.notes == "Observacao depois"
    kwargs = audit_event_service.record_write.await_args.kwargs
    assert kwargs["event_type"] == "ConsultationUpdated"
    assert kwargs["before_state"]["notes"] == "Observacao antes"
    assert kwargs["after_state"]["notes"] == "Observacao depois"


def test_consultation_service_list_linked_evolutions_uses_consultation_patient() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
    )
    evolution_repository = AsyncMock()
    evolution_repository.list_by_consultation.return_value = []
    service = ConsultationService(
        consultation_repository=consultation_repository,
        patient_repository=AsyncMock(),
        evolution_repository=evolution_repository,
    )

    asyncio.run(
        service.list_consultation_evolutions(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            page=1,
            page_size=20,
        )
    )

    evolution_repository.list_by_consultation.assert_awaited_once_with(
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=consultation_id,
        page=1,
        page_size=20,
    )


def test_consultation_service_create_requires_existing_patient() -> None:
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = None
    service = ConsultationService(
        consultation_repository=AsyncMock(),
        patient_repository=patient_repository,
    )

    try:
        asyncio.run(
            service.create_consultation(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateConsultationInput(),
            )
        )
    except ConsultationPatientNotFoundError as exc:
        assert str(exc) == "Patient not found"
    else:
        raise AssertionError("Expected missing patient to raise not found")


def test_consultation_service_create_defaults_schedule_end_date_and_status() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    scheduled_start_at = datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc)
    repository = AsyncMock()
    repository.has_schedule_overlap.return_value = False
    repository.create.side_effect = lambda consultation: consultation
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    created = asyncio.run(
        service.create_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateConsultationInput(
                scheduled_start_at=scheduled_start_at,
                diagnosis="Dermatite",
                notes="Retornar com exames",
            ),
        )
    )

    assert created.consultation_date == date(2026, 6, 10)
    assert created.scheduled_end_at == scheduled_start_at + timedelta(minutes=30)
    assert created.status == CONSULTATION_STATUS_SCHEDULED
    assert created.diagnosis == "Dermatite"
    assert created.notes == "Retornar com exames"


def test_consultation_service_create_copies_latest_medical_history_and_medications() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    previous_consultation_id = uuid4()
    new_consultation_id = uuid4()
    repository = AsyncMock()
    repository.get_latest_by_patient.return_value = Consultation(
        id=previous_consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 10),
    )
    repository.has_schedule_overlap.return_value = False
    repository.create.side_effect = lambda consultation: Consultation(
        id=new_consultation_id,
        doctor_id=consultation.doctor_id,
        patient_id=consultation.patient_id,
        consultation_date=consultation.consultation_date,
        scheduled_start_at=consultation.scheduled_start_at,
        scheduled_end_at=consultation.scheduled_end_at,
        status=consultation.status,
        diagnosis=consultation.diagnosis,
        notes=consultation.notes,
        chief_complaint=consultation.chief_complaint,
        physical_exam=consultation.physical_exam,
        conduct=consultation.conduct,
        created_at=consultation.created_at,
    )
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    medical_history_repository = AsyncMock()
    medical_history_repository.get_latest_for_consultation.return_value = MedicalHistory(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=previous_consultation_id,
        body="Asma",
    )
    medical_history_repository.create.side_effect = lambda history: history
    continuous_medication_repository = AsyncMock()
    continuous_medication_repository.list_by_consultation.return_value = [
        ContinuousMedication(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=previous_consultation_id,
            name="Losartana",
            dosage="50mg",
            status="active",
        )
    ]
    continuous_medication_repository.create.side_effect = lambda medication: medication
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
        medical_history_repository=medical_history_repository,
        continuous_medication_repository=continuous_medication_repository,
    )

    created = asyncio.run(
        service.create_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateConsultationInput(consultation_date=date(2026, 6, 20)),
        )
    )

    assert created.id == new_consultation_id
    copied_history = medical_history_repository.create.await_args.args[0]
    assert copied_history.consultation_id == new_consultation_id
    assert copied_history.body == "Asma"
    copied_medication = continuous_medication_repository.create.await_args.args[0]
    assert copied_medication.consultation_id == new_consultation_id
    assert copied_medication.name == "Losartana"


def test_consultation_service_create_overrides_copied_snapshots_with_payload() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    previous_consultation_id = uuid4()
    new_consultation_id = uuid4()
    repository = AsyncMock()
    repository.get_latest_by_patient.return_value = Consultation(
        id=previous_consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 10),
    )
    repository.has_schedule_overlap.return_value = False
    repository.create.side_effect = lambda consultation: Consultation(
        id=new_consultation_id,
        doctor_id=consultation.doctor_id,
        patient_id=consultation.patient_id,
        consultation_date=consultation.consultation_date,
    )
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    copied_history = MedicalHistory(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=new_consultation_id,
        body="Asma",
    )
    medical_history_repository = AsyncMock()
    medical_history_repository.get_latest_for_consultation.return_value = MedicalHistory(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=previous_consultation_id,
        body="Asma",
    )
    medical_history_repository.create.side_effect = lambda history: copied_history
    medical_history_repository.list_by_patient.return_value = [copied_history]
    medical_history_repository.update.side_effect = lambda history: history
    copied_medication = ContinuousMedication(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=new_consultation_id,
        name="Losartana",
        dosage="50mg",
        status="active",
    )
    continuous_medication_repository = AsyncMock()
    continuous_medication_repository.list_by_consultation.side_effect = [
        [
            ContinuousMedication(
                id=uuid4(),
                doctor_id=doctor_id,
                patient_id=patient_id,
                consultation_id=previous_consultation_id,
                name="Losartana",
                dosage="50mg",
                status="active",
            )
        ],
        [copied_medication],
    ]
    continuous_medication_repository.create.side_effect = lambda medication: medication
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
        medical_history_repository=medical_history_repository,
        continuous_medication_repository=continuous_medication_repository,
    )

    asyncio.run(
        service.create_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateConsultationInput(
                consultation_date=date(2026, 6, 20),
                medical_history_body="Novo antecedente",
                continuous_medications=[
                    ConsultationMedicationInput(
                        name="Metformina",
                        dosage="500mg",
                        active=True,
                    )
                ],
            ),
        )
    )

    updated_history = medical_history_repository.update.await_args.args[0]
    assert updated_history.body == "Novo antecedente"
    created_medication = continuous_medication_repository.create.await_args.args[0]
    assert created_medication.name == "Metformina"
    continuous_medication_repository.delete.assert_awaited_once_with(
        doctor_id=doctor_id,
        medication_id=copied_medication.id,
    )


def test_consultation_service_create_without_previous_consultation_skips_snapshot_copy() -> None:
    repository = AsyncMock()
    repository.get_latest_by_patient.return_value = None
    repository.has_schedule_overlap.return_value = False
    repository.create.side_effect = lambda consultation: consultation
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    medical_history_repository = AsyncMock()
    continuous_medication_repository = AsyncMock()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
        medical_history_repository=medical_history_repository,
        continuous_medication_repository=continuous_medication_repository,
    )

    asyncio.run(
        service.create_consultation(
            doctor_id=uuid4(),
            patient_id=uuid4(),
            payload=CreateConsultationInput(consultation_date=date(2026, 6, 20)),
        )
    )

    medical_history_repository.get_latest_for_consultation.assert_not_awaited()
    continuous_medication_repository.list_by_consultation.assert_not_awaited()


def test_consultation_service_copy_latest_consultation_copies_only_clinical_fields() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    latest = Consultation(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 20),
        scheduled_start_at=datetime(2026, 6, 20, 14, 0, tzinfo=timezone.utc),
        scheduled_end_at=datetime(2026, 6, 20, 14, 30, tzinfo=timezone.utc),
        status=CONSULTATION_STATUS_COMPLETED,
        diagnosis="Rosácea",
        notes="Copiar observacao clinica",
        chief_complaint="Piora",
        physical_exam="Exame",
        conduct="Conduta",
    )
    repository = AsyncMock()
    repository.get_latest_by_patient.return_value = latest
    repository.has_schedule_overlap.return_value = False
    repository.create.side_effect = lambda consultation: consultation
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    copied = asyncio.run(
        service.copy_latest_consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
    )

    assert copied.id != latest.id
    assert copied.consultation_date == date.today()
    assert copied.scheduled_start_at is None
    assert copied.scheduled_end_at is None
    assert copied.status == CONSULTATION_STATUS_SCHEDULED
    assert copied.diagnosis == "Rosácea"
    assert copied.notes == "Copiar observacao clinica"
    assert copied.chief_complaint == "Piora"
    assert copied.physical_exam == "Exame"
    assert copied.conduct == "Conduta"


def test_consultation_service_copy_latest_requires_existing_source() -> None:
    repository = AsyncMock()
    repository.get_latest_by_patient.return_value = None
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    try:
        asyncio.run(
            service.copy_latest_consultation(
                doctor_id=uuid4(),
                patient_id=uuid4(),
            )
        )
    except ConsultationCopySourceNotFoundError as exc:
        assert str(exc) == "No consultation available to copy"
    else:
        raise AssertionError("Expected missing source consultation to raise an error")


def test_consultation_service_update_preserves_omitted_fields() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    created_at = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    existing = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 2),
        scheduled_start_at=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
        scheduled_end_at=datetime(2026, 6, 2, 9, 45, tzinfo=timezone.utc),
        status=CONSULTATION_STATUS_COMPLETED,
        notes="Observacao mantida",
        chief_complaint="Antes",
        physical_exam="Exame antes",
        conduct="Conduta antes",
        created_at=created_at,
    )
    repository = AsyncMock()
    repository.get_by_id.return_value = existing
    repository.has_schedule_overlap.return_value = False
    repository.update.side_effect = lambda consultation: consultation
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=AsyncMock(),
    )

    saved = asyncio.run(
        service.update_consultation(
            doctor_id=doctor_id,
            consultation_id=consultation_id,
            payload=UpdateConsultationInput(fields={"chief_complaint": "Depois"}),
        )
    )

    assert saved.chief_complaint == "Depois"
    assert saved.notes == "Observacao mantida"
    assert saved.physical_exam == "Exame antes"
    assert saved.conduct == "Conduta antes"
    assert saved.scheduled_start_at == existing.scheduled_start_at
    assert saved.scheduled_end_at == existing.scheduled_end_at
    assert saved.status == CONSULTATION_STATUS_COMPLETED


def test_consultation_service_create_rejects_naive_schedule_datetime() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    try:
        asyncio.run(
            service.create_consultation(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateConsultationInput(
                    scheduled_start_at=datetime(2026, 6, 10, 13, 0),
                ),
            )
        )
    except ConsultationValidationError as exc:
        assert str(exc) == "scheduled_start_at must include timezone"
    else:
        raise AssertionError("Expected naive datetime to be rejected")


def test_consultation_service_create_rejects_invalid_schedule_range() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    try:
        asyncio.run(
            service.create_consultation(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateConsultationInput(
                    scheduled_start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
                    scheduled_end_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
                ),
            )
        )
    except ConsultationValidationError as exc:
        assert str(exc) == "scheduled_end_at must be greater than scheduled_start_at"
    else:
        raise AssertionError("Expected invalid schedule range to be rejected")


def test_consultation_service_create_blocks_overlapping_schedule() -> None:
    repository = AsyncMock()
    repository.has_schedule_overlap.return_value = True
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    try:
        asyncio.run(
            service.create_consultation(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateConsultationInput(
                    scheduled_start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
                    scheduled_end_at=datetime(2026, 6, 10, 13, 30, tzinfo=timezone.utc),
                    status=CONSULTATION_STATUS_COMPLETED,
                ),
            )
        )
    except ConsultationScheduleConflictError as exc:
        assert str(exc) == "Consultation schedule overlaps an existing consultation"
    else:
        raise AssertionError("Expected overlap to be rejected")


def test_consultation_service_create_allows_cancelled_overlap() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = object()
    repository.create.side_effect = lambda consultation: consultation
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=patient_repository,
    )

    created = asyncio.run(
        service.create_consultation(
            doctor_id=uuid4(),
            patient_id=uuid4(),
            payload=CreateConsultationInput(
                scheduled_start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
                scheduled_end_at=datetime(2026, 6, 10, 13, 30, tzinfo=timezone.utc),
                status=CONSULTATION_STATUS_CANCELLED,
            ),
        )
    )

    assert created.status == CONSULTATION_STATUS_CANCELLED
    repository.has_schedule_overlap.assert_not_awaited()


def test_consultation_service_list_by_interval_validates_and_filters() -> None:
    repository = AsyncMock()
    repository.list_by_doctor_interval.return_value = []
    service = ConsultationService(
        consultation_repository=repository,
        patient_repository=AsyncMock(),
    )
    doctor_id = uuid4()
    start_at = datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc)

    asyncio.run(
        service.list_consultations_by_interval(
            doctor_id=doctor_id,
            start_at=start_at,
            end_at=end_at,
            status=CONSULTATION_STATUS_SCHEDULED,
        )
    )

    repository.list_by_doctor_interval.assert_awaited_once_with(
        doctor_id=doctor_id,
        start_at=start_at,
        end_at=end_at,
        status=CONSULTATION_STATUS_SCHEDULED,
    )


def test_consultation_schema_rejects_naive_schedule_datetime() -> None:
    try:
        ConsultationCreateRequest(
            scheduled_start_at=datetime(2026, 6, 10, 13, 0),
        )
    except ValidationError as exc:
        assert "Datetime must include timezone" in str(exc)
    else:
        raise AssertionError("Expected schema to reject naive datetime")


def test_consultation_schema_accepts_notes() -> None:
    payload = ConsultationCreateRequest(
        notes="Observacao livre",
        scheduled_start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
    )

    assert payload.notes == "Observacao livre"


def test_consultation_repository_get_by_id_filters_by_doctor_and_optional_patient() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(row=None)
    repository = SQLAlchemyConsultationRepository(session=session)

    asyncio.run(
        repository.get_by_id(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            consultation_id=UUID("00000000-0000-0000-0000-000000000222"),
            patient_id=UUID("00000000-0000-0000-0000-000000000333"),
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    assert "WHERE consultation.id =" in compiled
    assert "consultation.doctor_id =" in compiled
    assert "consultation.patient_id =" in compiled


def test_consultation_repository_list_by_interval_filters_overlap_and_status() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(rows=[])
    repository = SQLAlchemyConsultationRepository(session=session)

    asyncio.run(
        repository.list_by_doctor_interval(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc),
            status=CONSULTATION_STATUS_SCHEDULED,
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    assert "consultation.scheduled_start_at <" in compiled
    assert "consultation.scheduled_end_at >" in compiled
    assert "consultation.status =" in compiled


def test_consultation_repository_overlap_ignores_cancelled_and_current_consultation() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(row=None)
    repository = SQLAlchemyConsultationRepository(session=session)

    asyncio.run(
        repository.has_schedule_overlap(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            scheduled_start_at=datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc),
            scheduled_end_at=datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc),
            exclude_consultation_id=UUID("00000000-0000-0000-0000-000000000222"),
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    assert "consultation.status !=" in compiled
    assert "consultation.id !=" in compiled


def test_evolution_repository_list_by_consultation_filters_order_and_pagination() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(rows=[])
    repository = SQLAlchemyEvolutionRepository(session=session)

    asyncio.run(
        repository.list_by_consultation(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            patient_id=UUID("00000000-0000-0000-0000-000000000222"),
            consultation_id=UUID("00000000-0000-0000-0000-000000000333"),
            page=2,
            page_size=5,
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    params = stmt.compile(dialect=postgresql.dialect()).params

    assert "WHERE evolution.doctor_id =" in compiled
    assert "evolution.patient_id =" in compiled
    assert "evolution.consultation_id =" in compiled
    assert "ORDER BY evolution.occurred_at DESC, evolution.created_at DESC" in compiled
    assert params["param_1"] == 5
    assert params["param_2"] == 5


def test_openapi_exposes_consultation_endpoints() -> None:
    app = create_app()
    try:
        schema = app.openapi()
    finally:
        asyncio.run(app.state.container.close())

    assert "/patients/{patient_id}/consultations" in schema["paths"]
    assert "post" in schema["paths"]["/patients/{patient_id}/consultations"]
    assert "get" in schema["paths"]["/patients/{patient_id}/consultations"]
    assert "/patients/{patient_id}/consultations/copy-latest" in schema["paths"]
    assert "post" in schema["paths"]["/patients/{patient_id}/consultations/copy-latest"]
    assert "/consultations/{consultation_id}" in schema["paths"]
    assert "/consultations" in schema["paths"]
    assert "get" in schema["paths"]["/consultations/{consultation_id}"]
    assert "put" in schema["paths"]["/consultations/{consultation_id}"]
    assert "delete" not in schema["paths"]["/consultations/{consultation_id}"]
    assert "/consultations/{consultation_id}/evolutions" in schema["paths"]
    assert "get" in schema["paths"]["/consultations/{consultation_id}/evolutions"]
    assert "get" in schema["paths"]["/consultations"]


def test_openapi_consultation_update_request_requires_contract_schema() -> None:
    app = create_app()
    try:
        schema = app.openapi()
    finally:
        asyncio.run(app.state.container.close())

    request_body = schema["paths"]["/consultations/{consultation_id}"]["put"]["requestBody"][
        "content"
    ]["application/json"]["schema"]
    assert request_body["$ref"] == "#/components/schemas/ConsultationUpdateRequest"
    properties = schema["components"]["schemas"]["ConsultationUpdateRequest"]["properties"]
    assert "medical_history_body" in properties
    assert "continuous_medications" in properties


def test_consultation_endpoints_contract_and_errors() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    occurred_at = datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc)
    service = AsyncMock()
    service.create_consultation.return_value = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_date=date(2026, 6, 4),
        scheduled_start_at=occurred_at,
        scheduled_end_at=occurred_at + timedelta(minutes=30),
        status=CONSULTATION_STATUS_SCHEDULED,
        diagnosis="Dermatite",
        notes="Levar resultados",
        chief_complaint="Queixa principal",
        physical_exam="Exame",
        conduct="Conduta",
        created_at=occurred_at,
    )
    service.list_consultations.return_value = [service.create_consultation.return_value]
    service.list_consultations_by_interval.return_value = [service.create_consultation.return_value]
    service.get_consultation.return_value = service.create_consultation.return_value
    service.update_consultation.return_value = service.create_consultation.return_value
    service.copy_latest_consultation.return_value = service.create_consultation.return_value
    service.list_consultation_evolutions.return_value = [
        Evolution(
            id=uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            consultation_id=consultation_id,
            origin_type="consultation",
            content="Conteudo clinico",
            occurred_at=occurred_at,
            created_at=occurred_at,
            updated_at=occurred_at,
        )
    ]

    app = create_app()
    app.dependency_overrides[get_authenticated_doctor] = lambda: AuthenticatedDoctor(doctor_id=doctor_id)
    app.dependency_overrides[get_consultation_service] = lambda: service

    with TestClient(app) as client:
        create_response = client.post(
            f"/patients/{patient_id}/consultations",
            json={
                "scheduled_start_at": "2026-06-04T14:30:00Z",
                "diagnosis": "Dermatite",
                "notes": "Levar resultados",
                "chief_complaint": "Queixa principal",
                "physical_exam": "Exame",
                "conduct": "Conduta",
                "medical_history_body": "HAS",
                "continuous_medications": [
                    {
                        "name": "Losartana",
                        "dosage": "50mg",
                        "active": True,
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["id"] == str(consultation_id)
        assert create_response.json()["status"] == CONSULTATION_STATUS_SCHEDULED
        assert create_response.json()["diagnosis"] == "Dermatite"
        assert create_response.json()["notes"] == "Levar resultados"
        create_payload = service.create_consultation.await_args.kwargs["payload"]
        assert create_payload.medical_history_body == "HAS"
        assert create_payload.continuous_medications[0].name == "Losartana"

        copy_response = client.post(f"/patients/{patient_id}/consultations/copy-latest")
        assert copy_response.status_code == 201

        list_response = client.get(f"/patients/{patient_id}/consultations?page=1&page_size=20")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        interval_response = client.get(
            "/consultations?start_at=2026-06-04T14:00:00Z&end_at=2026-06-04T15:00:00Z&status=scheduled"
        )
        assert interval_response.status_code == 200
        assert len(interval_response.json()) == 1

        detail_response = client.get(f"/consultations/{consultation_id}")
        assert detail_response.status_code == 200
        assert detail_response.json()["patient_id"] == str(patient_id)

        update_response = client.put(
            f"/consultations/{consultation_id}",
            json={
                "chief_complaint": "Queixa principal atualizada",
                "continuous_medications": [],
            },
        )
        assert update_response.status_code == 200
        update_payload = service.update_consultation.await_args.kwargs["payload"]
        assert update_payload.fields["continuous_medications"] == []

        linked_evolutions_response = client.get(
            f"/consultations/{consultation_id}/evolutions?page=1&page_size=20"
        )
        assert linked_evolutions_response.status_code == 200
        assert len(linked_evolutions_response.json()) == 1

        service.get_consultation.side_effect = ConsultationNotFoundError("Consultation not found")
        not_found_response = client.get(f"/consultations/{uuid4()}")
        assert not_found_response.status_code == 404
        service.get_consultation.side_effect = None

        service.create_consultation.side_effect = ConsultationPatientNotFoundError("Patient not found")
        patient_missing_response = client.post(
            f"/patients/{patient_id}/consultations",
            json={
                "scheduled_start_at": "2026-06-04T14:30:00Z",
                "diagnosis": "Dermatite",
                "notes": "Levar resultados",
                "chief_complaint": "Queixa principal",
                "physical_exam": "Exame",
                "conduct": "Conduta",
            },
        )
        assert patient_missing_response.status_code == 404
        service.create_consultation.side_effect = None

        service.copy_latest_consultation.side_effect = ConsultationCopySourceNotFoundError(
            "No consultation available to copy"
        )
        copy_missing_response = client.post(f"/patients/{patient_id}/consultations/copy-latest")
        assert copy_missing_response.status_code == 404
        service.copy_latest_consultation.side_effect = None

        service.update_consultation.side_effect = ConsultationNotFoundError("Consultation not found")
        update_missing_response = client.put(
            f"/consultations/{consultation_id}",
            json={
                "chief_complaint": "Queixa principal",
            },
        )
        assert update_missing_response.status_code == 404
        service.update_consultation.side_effect = None

        service.create_consultation.side_effect = ConsultationValidationError(
            "scheduled_end_at must be greater than scheduled_start_at"
        )
        invalid_schedule_response = client.post(
            f"/patients/{patient_id}/consultations",
            json={
                "scheduled_start_at": "2026-06-04T14:30:00Z",
                "scheduled_end_at": "2026-06-04T14:00:00Z",
            },
        )
        assert invalid_schedule_response.status_code == 422
        service.create_consultation.side_effect = None

        service.update_consultation.side_effect = ConsultationScheduleConflictError(
            "Consultation schedule overlaps an existing consultation"
        )
        overlap_response = client.put(
            f"/consultations/{consultation_id}",
            json={"scheduled_start_at": "2026-06-04T14:30:00Z"},
        )
        assert overlap_response.status_code == 409
        service.update_consultation.side_effect = None

        service.list_consultations_by_interval.side_effect = ConsultationValidationError(
            "end_at must be greater than start_at"
        )
        interval_invalid_response = client.get(
            "/consultations?start_at=2026-06-04T15:00:00Z&end_at=2026-06-04T14:00:00Z"
        )
        assert interval_invalid_response.status_code == 422
        service.list_consultations_by_interval.side_effect = None

        service.list_consultation_evolutions.side_effect = ConsultationNotFoundError(
            "Consultation not found"
        )
        evolutions_missing_response = client.get(
            f"/consultations/{consultation_id}/evolutions?page=1&page_size=20"
        )
        assert evolutions_missing_response.status_code == 404

    app.dependency_overrides.clear()
