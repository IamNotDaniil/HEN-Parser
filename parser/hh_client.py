from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from parser.models import VacancyRecord, VacancySalary

BASE_URL = "https://api.hh.ru/vacancies"
DEFAULT_PER_PAGE = 20
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = "HEN-Parser/0.1 (+https://github.com/)"


class HHClient:
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({"User-Agent": user_agent})

    def search_vacancies(
        self,
        query: str,
        area: int | None = None,
        page: int = 0,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "text": query,
            "page": page,
            "per_page": per_page,
        }
        if area is not None:
            params["area"] = area

        response = self.session.get(BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def iter_vacancies(
        self,
        query: str,
        area: int | None = None,
        max_pages: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> list[VacancyRecord]:
        vacancies: list[VacancyRecord] = []
        for page in range(max_pages):
            payload = self.search_vacancies(query=query, area=area, page=page, per_page=per_page)
            items = payload.get("items", [])
            if not items:
                break
            for item in items:
                vacancies.append(self._build_record(item))
        return vacancies

    def _build_record(self, item: dict[str, Any]) -> VacancyRecord:
        salary_payload = item.get("salary")
        salary = None
        if salary_payload is not None:
            salary = VacancySalary(
                currency=salary_payload.get("currency"),
                gross=salary_payload.get("gross"),
                salary_from=salary_payload.get("from"),
                salary_to=salary_payload.get("to"),
            )

        published_at = item.get("published_at")
        parsed_published_at = None
        if published_at:
            parsed_published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        return VacancyRecord(
            vacancy_id=str(item.get("id")),
            source="hh.ru",
            title=item.get("name", ""),
            employer=(item.get("employer") or {}).get("name"),
            area=(item.get("area") or {}).get("name"),
            published_at=parsed_published_at,
            alternate_url=item.get("alternate_url"),
            snippet_requirement=(item.get("snippet") or {}).get("requirement"),
            snippet_responsibility=(item.get("snippet") or {}).get("responsibility"),
            schedule=(item.get("schedule") or {}).get("name"),
            experience=(item.get("experience") or {}).get("name"),
            employment=(item.get("employment") or {}).get("name"),
            salary=salary,
            raw_payload=item,
        )
