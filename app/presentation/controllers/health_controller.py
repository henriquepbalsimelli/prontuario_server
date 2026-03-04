from fastapi import APIRouter, Depends

from app.application.services.health_service import HealthService
from app.presentation.dependencies import get_health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def healthcheck(service: HealthService = Depends(get_health_service)) -> dict[str, str]:
    return service.execute()
