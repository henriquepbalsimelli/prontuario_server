from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Doctor:
    id: UUID
    name: str
    email: str
    password_hash: str
    preferences: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
