import json
import time
from typing import Any
from uuid import uuid4

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.presentation.request_context import clear_request_context, set_request_context

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_request_bodies: bool = True) -> None:
        super().__init__(app)
        self.log_request_bodies = log_request_bodies

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        set_request_context(
            request_id=request_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        body_payload: dict[str, Any] | list[Any] | None = None

        try:
            if self.log_request_bodies and request.method in {"POST", "PUT", "PATCH"}:
                body = await request.body()
                if body:
                    request._body = body
                    try:
                        body_payload = json.loads(body.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        body_payload = {"raw_body": "<non-json-body>"}

            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id

            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                status_code=response.status_code,
                duration_ms=round(elapsed_ms, 2),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_body=body_payload,
            )

            return response
        finally:
            structlog.contextvars.clear_contextvars()
            clear_request_context()
