from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.application.services.audit_event_service import AuditEventService
from app.application.services.patient_service import (
    CreatePatientInput,
    PatientService,
    UpdatePatientInput,
)
from app.domain.models.patient import Patient
from app.infrastructure.repositories.sqlalchemy_patient_repository import (
    SQLAlchemyPatientRepository,
)
from app.presentation.request_context import clear_request_context, set_request_context


class _ScalarResult:
    def __init__(self, row: object) -> None:
        self._row = row

    def all(self) -> list[object]:
        return []

    def one(self) -> object:
        return self._row

    def one_or_none(self) -> object:
        return self._row


class _ExecuteResult:
    def __init__(self, row: object = None, rowcount: int = 0) -> None:
        self._row = row
        self.rowcount = rowcount

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(self._row)

    def scalar_one(self) -> object:
        return self._row

    def scalar_one_or_none(self) -> object:
        return self._row


def test_record_write_commits_with_sanitized_event_payload() -> None:
    session = AsyncMock()
    session.add = Mock()
    event_bus = AsyncMock()
    service = AuditEventService(session=session, event_bus=event_bus)
    doctor_id = uuid4()
    entity_id = uuid4()
    before_state = {"notes": "sensivel"}
    after_state = {"notes": "alterado"}

    set_request_context(
        request_id="req-123",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    try:
        asyncio.run(
            service.record_write(
                doctor_id=doctor_id,
                entity_type="patient",
                entity_id=entity_id,
                action="update",
                event_type="PatientUpdated",
                before_state=before_state,
                after_state=after_state,
            )
        )
    finally:
        clear_request_context()

    audit = session.add.call_args.args[0]
    assert audit.doctor_id == doctor_id
    assert audit.entity_id == entity_id
    assert audit.before_state == before_state
    assert audit.after_state == after_state
    assert audit.request_id == "req-123"

    event_bus.publish.assert_awaited_once_with(
        event_type="PatientUpdated",
        entity_id=entity_id,
        payload={
            "entity_type": "patient",
            "entity_id": str(entity_id),
            "action": "update",
            "doctor_id": str(doctor_id),
            "request_id": "req-123",
        },
    )
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


def test_record_write_rolls_back_when_event_publish_fails() -> None:
    session = AsyncMock()
    session.add = Mock()
    event_bus = AsyncMock()
    event_bus.publish.side_effect = RuntimeError("publish failed")
    service = AuditEventService(session=session, event_bus=event_bus)

    try:
        asyncio.run(
            service.record_write(
                doctor_id=uuid4(),
                entity_type="patient",
                entity_id=uuid4(),
                action="create",
                event_type="PatientCreated",
                before_state=None,
                after_state={"name": "Fulano"},
            )
        )
    except RuntimeError as exc:
        assert str(exc) == "publish failed"
    else:
        raise AssertionError("record_write should propagate the publish failure")

    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


def test_record_write_rolls_back_when_commit_fails() -> None:
    session = AsyncMock()
    session.add = Mock()
    session.commit.side_effect = RuntimeError("commit failed")
    event_bus = AsyncMock()
    service = AuditEventService(session=session, event_bus=event_bus)

    try:
        asyncio.run(
            service.record_write(
                doctor_id=uuid4(),
                entity_type="patient",
                entity_id=uuid4(),
                action="delete",
                event_type="PatientDeleted",
                before_state={"name": "Fulano"},
                after_state=None,
            )
        )
    except RuntimeError as exc:
        assert str(exc) == "commit failed"
    else:
        raise AssertionError("record_write should propagate the commit failure")

    event_bus.publish.assert_awaited_once()
    session.rollback.assert_awaited_once()


def test_patient_repository_create_uses_flush_without_commit() -> None:
    patient = Patient(id=uuid4(), doctor_id=uuid4(), name="Paciente")
    session = AsyncMock()
    session.add = Mock()
    repository = SQLAlchemyPatientRepository(session=session)

    asyncio.run(repository.create(patient=patient))

    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_patient_repository_update_uses_flush_without_commit() -> None:
    patient = Patient(id=uuid4(), doctor_id=uuid4(), name="Paciente atualizado")
    row = type(
        "PatientRow",
        (),
        {
            "id": patient.id,
            "doctor_id": patient.doctor_id,
            "name": "Paciente antigo",
            "birth_date": None,
            "gender": None,
            "phone": None,
            "notes": None,
            "created_at": None,
        },
    )()
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(row=row)
    repository = SQLAlchemyPatientRepository(session=session)

    asyncio.run(repository.update(patient=patient))

    assert row.name == "Paciente atualizado"
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(row)
    session.commit.assert_not_awaited()


def test_patient_repository_delete_uses_flush_without_commit() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(rowcount=1)
    repository = SQLAlchemyPatientRepository(session=session)

    deleted = asyncio.run(repository.delete(doctor_id=uuid4(), patient_id=uuid4()))

    assert deleted is True
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_patient_service_create_records_audit() -> None:
    created = Patient(id=uuid4(), doctor_id=uuid4(), name="Maria", notes="clinico")
    repository = AsyncMock()
    repository.create.return_value = created
    audit_event_service = AsyncMock()
    service = PatientService(repository=repository, audit_event_service=audit_event_service)

    result = asyncio.run(
        service.create_patient(
            doctor_id=created.doctor_id,
            payload=CreatePatientInput(name="Maria", notes="clinico"),
        )
    )

    assert result == created
    audit_event_service.record_write.assert_awaited_once()
    kwargs = audit_event_service.record_write.await_args.kwargs
    assert kwargs["action"] == "create"
    assert kwargs["before_state"] is None
    assert kwargs["after_state"]["notes"] == "clinico"


def test_patient_service_update_records_audit() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    existing = Patient(id=patient_id, doctor_id=doctor_id, name="Maria", notes="antes")
    updated = Patient(id=patient_id, doctor_id=doctor_id, name="Maria", notes="depois")
    repository = AsyncMock()
    repository.get_by_id.return_value = existing
    repository.update.return_value = updated
    audit_event_service = AsyncMock()
    service = PatientService(repository=repository, audit_event_service=audit_event_service)

    result = asyncio.run(
        service.update_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=UpdatePatientInput(name="Maria", notes="depois"),
        )
    )

    assert result == updated
    kwargs = audit_event_service.record_write.await_args.kwargs
    assert kwargs["action"] == "update"
    assert kwargs["before_state"]["notes"] == "antes"
    assert kwargs["after_state"]["notes"] == "depois"


def test_patient_service_delete_records_audit() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    existing = Patient(id=patient_id, doctor_id=doctor_id, name="Maria", notes="antes")
    repository = AsyncMock()
    repository.get_by_id.return_value = existing
    repository.delete.return_value = True
    audit_event_service = AsyncMock()
    service = PatientService(repository=repository, audit_event_service=audit_event_service)

    asyncio.run(service.delete_patient(doctor_id=doctor_id, patient_id=patient_id))

    kwargs = audit_event_service.record_write.await_args.kwargs
    assert kwargs["action"] == "delete"
    assert kwargs["before_state"]["notes"] == "antes"
    assert kwargs["after_state"] is None
