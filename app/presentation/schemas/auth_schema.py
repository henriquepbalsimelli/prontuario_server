from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    doctor_id: UUID
    preferences: dict[str, Any] = Field(default_factory=dict)
    access_token: str
    token_type: str
    expires_in: int = Field(ge=1)
