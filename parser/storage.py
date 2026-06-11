from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from parser.models import VacancyRecord


class RawDataWriter:
    def __init__(self, output_dir: str = "data/raw") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, filename: str, vacancies: Iterable[VacancyRecord]) -> Path:
        target = self.output_dir / filename
        target.write_text(
            json.dumps([vacancy.to_dict() for vacancy in vacancies], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target

    def write_csv(self, filename: str, vacancies: Iterable[VacancyRecord]) -> Path:
        target = self.output_dir / filename
        rows = [vacancy.to_dict() for vacancy in vacancies]
        fieldnames = [
            "vacancy_id",
            "source",
            "title",
            "employer",
            "area",
            "published_at",
            "alternate_url",
            "snippet_requirement",
            "snippet_responsibility",
            "schedule",
            "experience",
            "employment",
        ]
        with target.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key) for key in fieldnames})
        return target
