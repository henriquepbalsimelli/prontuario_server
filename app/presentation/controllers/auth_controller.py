from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.auth_service import AuthService, InvalidCredentialsError, LoginInput
from app.presentation.dependencies import get_auth_service
from app.presentation.schemas.auth_schema import AuthLoginRequest, AuthTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: AuthLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    try:
        output = await service.login(payload=LoginInput(**payload.model_dump()))
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc

    return AuthTokenResponse(
        access_token=output.access_token,
        token_type=output.token_type,
        expires_in=output.expires_in,
    )
