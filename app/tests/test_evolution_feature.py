from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.application.services.evolution_service import (
    CreateEvolutionInput,
    EvolutionConsultationNotFoundError,
    EvolutionNotFoundError,
    EvolutionPatientNotFoundError,
    EvolutionService,
    EvolutionValidationError,
    UpdateEvolutionInput,
)
from app.domain.models.consultation import Consultation
from app.domain.models.evolution import Evolution
from app.domain.models.patient import Patient
from app.infrastructure.database.models import Evolution as EvolutionModel
from app.infrastructure.security.field_encryption import EncryptedString
from app.infrastructure.repositories.sqlalchemy_evolution_repository import (
    SQLAlchemyEvolutionRepository,
)
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_evolution_service
from app.presentation.main import create_app


class _ScalarResult:
    def __init__(self, rows: list[object] | None = None, row: object = None) -> None:
        self._rows = rows or []
        self._row = row

    def all(self) -> list[object]:
        return self._rows


class _ExecuteResult:
    def __init__(
        self,
        rows: list[object] | None = None,
        row: object = None,
    ) -> None:
        self._rows = rows or []
        self._row = row

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(rows=self._rows)

    def scalar_one_or_none(self) -> object:
        return self._row

    def scalar_one(self) -> object:
        return self._row


def test_evolution_service_creates_without_consultation() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    occurred_at = datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc)
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = Patient(id=patient_id, doctor_id=doctor_id, name="Maria")
    consultation_repository = AsyncMock()
    audit_event_service = AsyncMock()
    created = Evolution(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=None,
        origin_type="consultation",
        content="Conteudo clinico",
        occurred_at=occurred_at,
    )
    repository.create.return_value = created
    service = EvolutionService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )

    result = asyncio.run(
        service.create_evolution(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateEvolutionInput(
                consultation_id=None,
                origin_type="consultation",
                content="  Conteudo clinico  ",
                occurred_at=occurred_at,
            ),
        )
    )

    assert result == created
    repository.create.assert_awaited_once()
    saved = repository.create.await_args.kwargs["evolution"]
    assert saved.consultation_id is None
    assert saved.content == "Conteudo clinico"
    consultation_repository.get_by_id.assert_not_called()
    audit_event_service.record_write.assert_awaited_once()


def test_evolution_service_creates_with_matching_consultation() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    consultation_id = uuid4()
    occurred_at = datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc)
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = Patient(id=patient_id, doctor_id=doctor_id, name="Maria")
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = Consultation(
        id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
    )
    repository.create.return_value = Evolution(
        id=uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=consultation_id,
        origin_type="procedure",
        content="Conteudo",
        occurred_at=occurred_at,
    )
    service = EvolutionService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
    )

    asyncio.run(
        service.create_evolution(
            doctor_id=doctor_id,
            patient_id=patient_id,
            payload=CreateEvolutionInput(
                consultation_id=consultation_id,
                origin_type="procedure",
                content="Conteudo",
                occurred_at=occurred_at,
            ),
        )
    )

    consultation_repository.get_by_id.assert_awaited_once_with(
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=consultation_id,
    )


def test_evolution_service_rejects_incompatible_consultation() -> None:
    repository = AsyncMock()
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = Patient(id=uuid4(), doctor_id=uuid4(), name="Maria")
    consultation_repository = AsyncMock()
    consultation_repository.get_by_id.return_value = None
    service = EvolutionService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
    )

    try:
        asyncio.run(
            service.create_evolution(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateEvolutionInput(
                    consultation_id=uuid4(),
                    origin_type="consultation",
                    content="Conteudo",
                    occurred_at=datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc),
                ),
            )
        )
    except EvolutionConsultationNotFoundError as exc:
        assert str(exc) == "Consultation not found"
    else:
        raise AssertionError("Expected incompatible consultation to be rejected")


def test_evolution_service_rejects_blank_content() -> None:
    service = EvolutionService(
        repository=AsyncMock(),
        patient_repository=AsyncMock(),
        consultation_repository=AsyncMock(),
    )

    try:
        asyncio.run(
            service.create_evolution(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateEvolutionInput(
                    consultation_id=None,
                    origin_type="consultation",
                    content="   ",
                    occurred_at=datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc),
                ),
            )
        )
    except EvolutionValidationError as exc:
        assert str(exc) == "Content must not be empty"
    else:
        raise AssertionError("Expected blank content to be rejected")


def test_evolution_service_rejects_invalid_origin() -> None:
    patient_repository = AsyncMock()
    patient_repository.get_by_id.return_value = Patient(id=uuid4(), doctor_id=uuid4(), name="Maria")
    service = EvolutionService(
        repository=AsyncMock(),
        patient_repository=patient_repository,
        consultation_repository=AsyncMock(),
    )

    try:
        asyncio.run(
            service.create_evolution(
                doctor_id=uuid4(),
                patient_id=uuid4(),
                payload=CreateEvolutionInput(
                    consultation_id=None,
                    origin_type="invalid",
                    content="Conteudo",
                    occurred_at=datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc),
                ),
            )
        )
    except EvolutionValidationError as exc:
        assert str(exc) == "Invalid origin_type"
    else:
        raise AssertionError("Expected invalid origin to be rejected")


def test_evolution_service_preserves_identity_on_update_and_audits() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    evolution_id = uuid4()
    occurred_at = datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc)
    created_at = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    existing = Evolution(
        id=evolution_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=None,
        origin_type="consultation",
        content="Antes",
        occurred_at=occurred_at,
        created_at=created_at,
        updated_at=created_at,
    )
    updated = Evolution(
        id=evolution_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=None,
        origin_type="other",
        content="Depois",
        occurred_at=occurred_at,
        created_at=created_at,
        updated_at=occurred_at,
    )
    repository = AsyncMock()
    repository.get_by_id.return_value = existing
    repository.update.return_value = updated
    patient_repository = AsyncMock()
    consultation_repository = AsyncMock()
    audit_event_service = AsyncMock()
    service = EvolutionService(
        repository=repository,
        patient_repository=patient_repository,
        consultation_repository=consultation_repository,
        audit_event_service=audit_event_service,
    )

    result = asyncio.run(
        service.update_evolution(
            doctor_id=doctor_id,
            evolution_id=evolution_id,
            payload=UpdateEvolutionInput(
                consultation_id=None,
                origin_type="other",
                content="Depois",
                occurred_at=occurred_at,
            ),
        )
    )

    assert result == updated
    saved = repository.update.await_args.kwargs["evolution"]
    assert saved.id == evolution_id
    assert saved.doctor_id == doctor_id
    assert saved.patient_id == patient_id
    assert saved.created_at == created_at
    kwargs = audit_event_service.record_write.await_args.kwargs
    assert kwargs["event_type"] == "EvolutionUpdated"
    assert kwargs["before_state"]["content"] == "Antes"
    assert kwargs["after_state"]["content"] == "Depois"


def test_evolution_repository_list_applies_filters_order_and_pagination() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(rows=[])
    repository = SQLAlchemyEvolutionRepository(session=session)

    asyncio.run(
        repository.list_by_patient(
            doctor_id=UUID("00000000-0000-0000-0000-000000000111"),
            patient_id=UUID("00000000-0000-0000-0000-000000000222"),
            page=2,
            page_size=5,
        )
    )

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    params = stmt.compile(dialect=postgresql.dialect()).params

    assert "WHERE evolution.doctor_id =" in compiled
    assert "evolution.patient_id =" in compiled
    assert "ORDER BY evolution.occurred_at DESC, evolution.created_at DESC" in compiled
    assert params["param_1"] == 5
    assert params["param_2"] == 5


def test_evolution_repository_get_by_id_filters_by_doctor() -> None:
    session = AsyncMock()
    session.execute.return_value = _ExecuteResult(row=None)
    repository = SQLAlchemyEvolutionRepository(session=session)

    asyncio.run(repository.get_by_id(doctor_id=uuid4(), evolution_id=uuid4()))

    stmt = session.execute.await_args.args[0]
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
    assert "WHERE evolution.id =" in compiled
    assert "evolution.doctor_id =" in compiled


def test_evolution_content_uses_encrypted_string_column() -> None:
    assert isinstance(EvolutionModel.__table__.c.content.type, EncryptedString)


def test_openapi_exposes_evolution_endpoints() -> None:
    app = create_app()
    try:
        schema = app.openapi()
    finally:
        asyncio.run(app.state.container.close())

    assert "/patients/{patient_id}/evolutions" in schema["paths"]
    assert "post" in schema["paths"]["/patients/{patient_id}/evolutions"]
    assert "get" in schema["paths"]["/patients/{patient_id}/evolutions"]
    assert "/evolutions/{evolution_id}" in schema["paths"]
    assert "get" in schema["paths"]["/evolutions/{evolution_id}"]
    assert "put" in schema["paths"]["/evolutions/{evolution_id}"]
    assert "delete" not in schema["paths"]["/evolutions/{evolution_id}"]


def test_evolution_endpoints_contract_and_errors() -> None:
    doctor_id = uuid4()
    patient_id = uuid4()
    evolution_id = uuid4()
    occurred_at = datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc)
    service = AsyncMock()
    service.create_evolution.return_value = Evolution(
        id=evolution_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_id=None,
        origin_type="consultation",
        content="Conteudo clinico",
        occurred_at=occurred_at,
        created_at=occurred_at,
        updated_at=occurred_at,
    )
    service.list_evolutions.return_value = [service.create_evolution.return_value]
    service.get_evolution.return_value = service.create_evolution.return_value
    service.update_evolution.return_value = service.create_evolution.return_value

    app = create_app()
    app.dependency_overrides[get_authenticated_doctor] = lambda: AuthenticatedDoctor(doctor_id=doctor_id)
    app.dependency_overrides[get_evolution_service] = lambda: service

    with TestClient(app) as client:
        create_response = client.post(
            f"/patients/{patient_id}/evolutions",
            json={
                "consultation_id": None,
                "origin_type": "consultation",
                "content": "Conteudo clinico",
                "occurred_at": "2026-06-04T14:30:00Z",
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["id"] == str(evolution_id)

        list_response = client.get(f"/patients/{patient_id}/evolutions?page=1&page_size=20")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        detail_response = client.get(f"/evolutions/{evolution_id}")
        assert detail_response.status_code == 200
        assert detail_response.json()["patient_id"] == str(patient_id)

        update_response = client.put(
            f"/evolutions/{evolution_id}",
            json={
                "consultation_id": None,
                "origin_type": "other",
                "content": "Conteudo clinico atualizado",
                "occurred_at": "2026-06-04T15:30:00Z",
            },
        )
        assert update_response.status_code == 200

        invalid_origin_response = client.post(
            f"/patients/{patient_id}/evolutions",
            json={
                "consultation_id": None,
                "origin_type": "invalid",
                "content": "Conteudo clinico",
                "occurred_at": "2026-06-04T14:30:00Z",
            },
        )
        assert invalid_origin_response.status_code == 422

        service.get_evolution.side_effect = EvolutionNotFoundError("Evolution not found")
        not_found_response = client.get(f"/evolutions/{uuid4()}")
        assert not_found_response.status_code == 404
        service.get_evolution.side_effect = None

        service.create_evolution.side_effect = EvolutionPatientNotFoundError("Patient not found")
        patient_missing_response = client.post(
            f"/patients/{patient_id}/evolutions",
            json={
                "consultation_id": None,
                "origin_type": "consultation",
                "content": "Conteudo clinico",
                "occurred_at": "2026-06-04T14:30:00Z",
            },
        )
        assert patient_missing_response.status_code == 404
        service.create_evolution.side_effect = None

        service.update_evolution.side_effect = EvolutionConsultationNotFoundError(
            "Consultation not found"
        )
        consultation_missing_response = client.put(
            f"/evolutions/{evolution_id}",
            json={
                "consultation_id": str(uuid4()),
                "origin_type": "consultation",
                "content": "Conteudo clinico",
                "occurred_at": "2026-06-04T14:30:00Z",
            },
        )
        assert consultation_missing_response.status_code == 404

    app.dependency_overrides.clear()


def test_openapi_evolution_update_request_requires_all_editable_fields() -> None:
    app = create_app()
    try:
        schema = app.openapi()
    finally:
        asyncio.run(app.state.container.close())

    request_body = schema["paths"]["/evolutions/{evolution_id}"]["put"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert request_body["$ref"] == "#/components/schemas/EvolutionUpdateRequest"
