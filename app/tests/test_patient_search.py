from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql

from app.application.services.patient_service import (
    CreatePatientInput,
    PatientService,
    UpdatePatientInput,
)
from app.domain.models.patient import Patient
from app.infrastructure.repositories.sqlalchemy_patient_repository import (
    SQLAlchemyPatientRepository,
)


class _ScalarResult:
    def all(self) -> list[object]:
        return []


class _ExecuteResult:
    def scalars(self) -> _ScalarResult:
        return _ScalarResult()


def test_patient_service_forwards_normalized_name_filter() -> None:
    repository = AsyncMock()
    repository.list_by_doctor.return_value = []
    service = PatientService(repository=repository)
    doctor_id = uuid4()

    asyncio.run(
        service.list_patients(
            doctor_id=doctor_id,
            page=2,
            page_size=10,
            name="  henrique  ",
        )
    )

    repository.list_by_doctor.assert_awaited_once_with(
        doctor_id=doctor_id,
        page=2,
        page_size=10,
        name="henrique",
    )


def test_patient_service_converts_blank_name_filter_to_none() -> None:
    repository = AsyncMock()
    repository.list_by_doctor.return_value = []
    service = PatientService(repository=repository)

    asyncio.run(
        service.list_patients(
            doctor_id=uuid4(),
            page=1,
            page_size=10,
            name="   ",
        )
    )

    assert repository.list_by_doctor.await_args.kwargs["name"] is None


def test_repository_uses_default_order_without_name_filter() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult()
    repository = SQLAlchemyPatientRepository(session=session)

    asyncio.run(repository.list_by_doctor(doctor_id=uuid4(), page=2, page_size=5))

    stmt = session.execute.await_args.args[0]
    compiled = _compile_sql(stmt)
    params = stmt.compile(dialect=postgresql.dialect()).params

    assert "WHERE patient.doctor_id =" in compiled
    assert "ORDER BY patient.created_at DESC" in compiled
    assert "patient.name ILIKE" not in compiled
    assert params["param_1"] == 5
    assert params["param_2"] == 5


def test_repository_applies_case_insensitive_name_filter_and_name_order() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult()
    repository = SQLAlchemyPatientRepository(session=session)

    asyncio.run(
        repository.list_by_doctor(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            page=3,
            page_size=10,
            name="Hen",
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = _compile_sql(stmt)
    params = session.execute.await_args.args[0].compile(
        dialect=postgresql.dialect(),
    ).params

    assert "WHERE patient.doctor_id =" in compiled
    assert "patient.name ILIKE" in compiled
    assert "ORDER BY patient.name ASC" in compiled
    assert "ORDER BY patient.created_at DESC" not in compiled
    assert params["param_1"] == 10
    assert params["param_2"] == 20
    assert any(value == "%Hen%" for value in params.values())


def test_patient_service_preserves_medical_history_in_create_and_update() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    repository = AsyncMock()
    repository.create.side_effect = lambda patient: patient
    repository.get_by_id.return_value = Patient(
        id=patient_id,
        doctor_id=doctor_id,
        name="Maria",
        medical_history="asma",
        notes="contexto",
    )
    repository.update.side_effect = lambda patient: patient
    service = PatientService(repository=repository)

    created = asyncio.run(
        service.create_patient(
            doctor_id=doctor_id,
            payload=CreatePatientInput(
                name="Maria",
                medical_history="asma",
                notes="contexto",
            ),
        )
    )
    updated = asyncio.run(
        service.update_patient(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=UpdatePatientInput(
                name="Maria",
                medical_history="diabetes",
                notes="contexto",
            ),
        )
    )

    assert created.medical_history == "asma"
    assert updated.medical_history == "diabetes"


def _compile_sql(stmt: object) -> str:
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
