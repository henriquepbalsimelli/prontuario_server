from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.domain.interfaces.doctor_repository import DoctorRepository
from app.infrastructure.security.password_hashing import verify_password


class InvalidCredentialsError(Exception):
    pass


@dataclass(slots=True)
class LoginInput:
    email: str
    password: str


@dataclass(slots=True)
class LoginOutput:
    access_token: str
    token_type: str
    expires_in: int


class AuthService:
    def __init__(
        self,
        repository: DoctorRepository,
        jwt_secret_key: str,
        jwt_algorithm: str,
        jwt_access_token_exp_minutes: int,
    ) -> None:
        self.repository = repository
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.jwt_access_token_exp_minutes = jwt_access_token_exp_minutes

    async def login(self, payload: LoginInput) -> LoginOutput:
        normalized_email = payload.email.strip().lower()
        doctor = await self.repository.get_by_email(email=normalized_email)
        if doctor is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(plain_password=payload.password, stored_hash=doctor.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        expires_in = self.jwt_access_token_exp_minutes * 60
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=expires_in)
        token = jwt.encode(
            {
                "doctor_id": str(doctor.id),
                "sub": str(doctor.id),
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
        )

        return LoginOutput(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
        )
