from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class RequestContext:
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    doctor_id: UUID | None = None


_request_context_var: ContextVar[RequestContext] = ContextVar(
    "request_context",
    default=RequestContext(),
)


def get_request_context() -> RequestContext:
    return _request_context_var.get()


def set_request_context(**kwargs) -> RequestContext:
    current = _request_context_var.get()
    updated = RequestContext(
        request_id=kwargs.get("request_id", current.request_id),
        ip_address=kwargs.get("ip_address", current.ip_address),
        user_agent=kwargs.get("user_agent", current.user_agent),
        doctor_id=kwargs.get("doctor_id", current.doctor_id),
    )
    _request_context_var.set(updated)
    return updated


def clear_request_context() -> None:
    _request_context_var.set(RequestContext())
