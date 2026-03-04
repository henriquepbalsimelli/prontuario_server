from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response


class HTTPSAndHSTSMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        enforce_https: bool,
        hsts_enabled: bool,
        hsts_value: str,
    ) -> None:
        super().__init__(app)
        self.enforce_https = enforce_https
        self.hsts_enabled = hsts_enabled
        self.hsts_value = hsts_value

    @staticmethod
    def _is_https_request(request: Request) -> bool:
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            first_hop_proto = forwarded_proto.split(",")[0].strip().lower()
            return first_hop_proto == "https"

        return request.url.scheme.lower() == "https"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        is_https = self._is_https_request(request)

        if self.enforce_https and not is_https:
            secure_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(secure_url), status_code=307)

        response = await call_next(request)

        if self.hsts_enabled and is_https:
            response.headers["Strict-Transport-Security"] = self.hsts_value

        return response
