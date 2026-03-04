from dataclasses import dataclass
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.infrastructure.settings import Settings, get_settings
from app.presentation.request_context import set_request_context

bearer_scheme = HTTPBearer(auto_error=True)


@dataclass(slots=True)
class AuthenticatedDoctor:
    doctor_id: UUID


def get_authenticated_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedDoctor:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    doctor_id_raw = payload.get("doctor_id") or payload.get("sub")
    if doctor_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing doctor_id",
        )

    try:
        doctor_id = UUID(str(doctor_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid doctor_id in token",
        ) from exc

    set_request_context(doctor_id=doctor_id)
    structlog.contextvars.bind_contextvars(doctor_id=str(doctor_id))

    return AuthenticatedDoctor(doctor_id=doctor_id)
