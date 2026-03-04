from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Medication:
    id: UUID
    name: str
    active_principle: str | None = None
    form: str | None = None
    notes: str | None = None
