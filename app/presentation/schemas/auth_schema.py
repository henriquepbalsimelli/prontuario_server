from pydantic import BaseModel, EmailStr, Field


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int = Field(ge=1)
