from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.consultation_service import ConsultationPatientNotFoundError
from app.application.services.timeline_service import TimelineService
from app.presentation.auth import AuthenticatedDoctor, get_authenticated_doctor
from app.presentation.dependencies import get_timeline_service
from app.presentation.schemas.timeline_schema import TimelineEventResponse

router = APIRouter(tags=["timeline"])


@router.get("/patients/{patient_id}/timeline", response_model=list[TimelineEventResponse])
async def list_timeline(
    patient_id: UUID,
    types: list[str] | None = Query(default=None),
    doctor: AuthenticatedDoctor = Depends(get_authenticated_doctor),
    service: TimelineService = Depends(get_timeline_service),
) -> list[TimelineEventResponse]:
    try:
        events = await service.list_timeline(doctor.doctor_id, patient_id, types)
    except ConsultationPatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [TimelineEventResponse.model_validate(item) for item in events]
