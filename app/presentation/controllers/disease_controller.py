from fastapi import APIRouter, Depends, Query, status

from app.application.services.disease_service import CreateDiseaseInput, DiseaseService
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_disease_service
from app.presentation.schemas.disease_schema import DiseaseCreateRequest, DiseaseResponse

router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("", response_model=list[DiseaseResponse])
async def list_diseases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DiseaseService = Depends(get_disease_service),
) -> list[DiseaseResponse]:
    diseases = await service.list_diseases(page=page, page_size=page_size)
    return [DiseaseResponse.model_validate(item) for item in diseases]


@router.post("", response_model=DiseaseResponse, status_code=status.HTTP_201_CREATED)
async def create_disease(
    payload: DiseaseCreateRequest,
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: DiseaseService = Depends(get_disease_service),
) -> DiseaseResponse:
    disease = await service.create_disease(
        actor_doctor_id=doctor.doctor_id,
        payload=CreateDiseaseInput(**payload.model_dump()),
    )
    return DiseaseResponse.model_validate(disease)
