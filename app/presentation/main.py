from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from app.application.container import Container
from app.infrastructure.logging import configure_logging
from app.infrastructure.observability import configure_observability
from app.infrastructure.settings import get_settings
from app.presentation.controllers.consultation_controller import router as consultation_router
from app.presentation.controllers.auth_controller import router as auth_router
from app.presentation.controllers.disease_controller import router as disease_router
from app.presentation.controllers.doctor_controller import router as doctor_router
from app.presentation.controllers.health_controller import router as health_router
from app.presentation.controllers.image_controller import router as image_router
from app.presentation.controllers.lesion_controller import router as lesion_router
from app.presentation.controllers.medication_controller import router as medication_router
from app.presentation.controllers.patient_controller import router as patient_router
from app.presentation.middlewares.request_logging import RequestLoggingMiddleware
from app.presentation.middlewares.security import HTTPSAndHSTSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.container.close()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        json_logs=settings.log_json,
        trace_correlation_enabled=settings.log_trace_correlation_enabled,
        log_file_path=settings.log_file_path,
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )

    if settings.gzip_enabled:
        app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_bodies=settings.log_request_bodies,
    )
    app.add_middleware(
        HTTPSAndHSTSMiddleware,
        enforce_https=settings.enforce_https,
        hsts_enabled=settings.hsts_enabled,
        hsts_value=settings.hsts_value,
    )

    app.state.container = Container(settings=settings)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(doctor_router, prefix=settings.api_prefix)
    app.include_router(patient_router, prefix=settings.api_prefix)
    app.include_router(consultation_router, prefix=settings.api_prefix)
    app.include_router(disease_router, prefix=settings.api_prefix)
    app.include_router(medication_router, prefix=settings.api_prefix)
    app.include_router(image_router, prefix=settings.api_prefix)
    app.include_router(lesion_router, prefix=settings.api_prefix)
    configure_observability(
        app=app,
        settings=settings,
        engine=app.state.container.engine,
    )

    return app


app = create_app()
