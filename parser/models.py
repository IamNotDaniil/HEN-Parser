from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class VacancySalary:
    currency: str | None
    gross: bool | None
    salary_from: int | None
    salary_to: int | None


@dataclass(slots=True)
class VacancyRecord:
    vacancy_id: str
    source: str
    title: str
    employer: str | None
    area: str | None
    published_at: datetime | None
    alternate_url: str | None
    snippet_requirement: str | None
    snippet_responsibility: str | None
    schedule: str | None
    experience: str | None
    employment: str | None
    salary: VacancySalary | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.published_at is not None:
            payload["published_at"] = self.published_at.isoformat()
        return payload
