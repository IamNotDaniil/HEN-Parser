from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from parser.models import VacancyRecord, VacancySalary
from parser.storage import RawDataWriter


class RawDataWriterTest(unittest.TestCase):
    def test_write_json_and_csv_exports_flat_vacancy_fields(self) -> None:
        vacancy = VacancyRecord(
            vacancy_id="123",
            source="hh.ru",
            title="Python Developer",
            employer="Example Inc",
            area="Moscow",
            published_at=datetime(2026, 6, 11, tzinfo=UTC),
            alternate_url="https://example.test/vacancies/123",
            snippet_requirement="Python, SQL",
            snippet_responsibility="Build services",
            schedule="Удаленная работа",
            experience="1–3 года",
            employment="Полная занятость",
            salary=VacancySalary(currency="RUR", gross=False, salary_from=100000, salary_to=150000),
            raw_payload={"id": "123"},
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = RawDataWriter(output_dir=tmp_dir)
            json_path = writer.write_json("vacancies.json", [vacancy])
            csv_path = writer.write_csv("vacancies.csv", [vacancy])

            json_payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
            self.assertEqual(json_payload[0]["vacancy_id"], "123")
            self.assertEqual(json_payload[0]["salary"]["salary_from"], 100000)
            self.assertEqual(json_payload[0]["published_at"], "2026-06-11T00:00:00+00:00")

            with Path(csv_path).open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(rows[0]["title"], "Python Developer")
            self.assertEqual(rows[0]["employer"], "Example Inc")
            self.assertEqual(rows[0]["area"], "Moscow")


if __name__ == "__main__":
    unittest.main()
