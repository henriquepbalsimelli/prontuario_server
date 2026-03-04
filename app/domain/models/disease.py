from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Disease:
    id: UUID
    name: str
    cid10: str | None = None
    description: str | None = None
