from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.types.json import Jsonb


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    dsn: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return cls(dsn=database_url)

        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        dbname = os.getenv("POSTGRES_DB", "hen_parser")
        user = os.getenv("POSTGRES_USER", "hen_parser")
        password = os.getenv("POSTGRES_PASSWORD", "hen_parser")
        return cls(dsn=f"host={host} port={port} dbname={dbname} user={user} password={password}")


@dataclass(frozen=True, slots=True)
class ImportSummary:
    run_id: int
    fetched_count: int
    imported_count: int


class RawVacancyImporter:
    def __init__(self, connection: Connection[Any]) -> None:
        self.connection = connection

    def import_file(self, path: Path, query: str, area_code: int | None = None) -> ImportSummary:
        vacancies = self._read_vacancies(path)
        with self.connection.transaction():
            run_id = self._create_source_run(query=query, area_code=area_code)
            imported_count = 0
            for vacancy in vacancies:
                self._upsert_vacancy(vacancy)
                imported_count += 1
            self._finish_source_run(run_id=run_id, fetched_count=len(vacancies), status="completed")
        return ImportSummary(run_id=run_id, fetched_count=len(vacancies), imported_count=imported_count)

    def _read_vacancies(self, path: Path) -> list[dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Raw export must contain a JSON list: {path}")
        return payload

    def _create_source_run(self, query: str, area_code: int | None) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO source_runs (source_name, query, area_code)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("hh.ru", query, area_code),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create source run")
        return int(row[0])

    def _finish_source_run(self, run_id: int, fetched_count: int, status: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE source_runs
                SET finished_at = NOW(), fetched_count = %s, status = %s
                WHERE id = %s
                """,
                (fetched_count, status, run_id),
            )

    def _upsert_vacancy(self, vacancy: dict[str, Any]) -> None:
        company_id = self._upsert_company(vacancy.get("employer"))
        location_id = self._upsert_location(vacancy.get("area"))
        vacancy_id = self._upsert_vacancy_row(vacancy=vacancy, company_id=company_id, location_id=location_id)
        self._insert_salary_snapshot(vacancy_id=vacancy_id, salary=vacancy.get("salary"))

    def _upsert_company(self, name: str | None) -> int | None:
        if not name:
            return None
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO companies (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (name,),
            )
            row = cursor.fetchone()
        return int(row[0]) if row else None

    def _upsert_location(self, name: str | None) -> int | None:
        if not name:
            return None
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO locations (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (name,),
            )
            row = cursor.fetchone()
        return int(row[0]) if row else None

    def _upsert_vacancy_row(
        self,
        vacancy: dict[str, Any],
        company_id: int | None,
        location_id: int | None,
    ) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vacancies (
                    source_name,
                    source_vacancy_id,
                    company_id,
                    location_id,
                    title,
                    alternate_url,
                    published_at,
                    schedule,
                    experience,
                    employment,
                    snippet_requirement,
                    snippet_responsibility,
                    raw_payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_name, source_vacancy_id) DO UPDATE SET
                    company_id = EXCLUDED.company_id,
                    location_id = EXCLUDED.location_id,
                    title = EXCLUDED.title,
                    alternate_url = EXCLUDED.alternate_url,
                    published_at = EXCLUDED.published_at,
                    schedule = EXCLUDED.schedule,
                    experience = EXCLUDED.experience,
                    employment = EXCLUDED.employment,
                    snippet_requirement = EXCLUDED.snippet_requirement,
                    snippet_responsibility = EXCLUDED.snippet_responsibility,
                    raw_payload = EXCLUDED.raw_payload
                RETURNING id
                """,
                (
                    vacancy.get("source", "hh.ru"),
                    vacancy.get("vacancy_id"),
                    company_id,
                    location_id,
                    vacancy.get("title", ""),
                    vacancy.get("alternate_url"),
                    vacancy.get("published_at"),
                    vacancy.get("schedule"),
                    vacancy.get("experience"),
                    vacancy.get("employment"),
                    vacancy.get("snippet_requirement"),
                    vacancy.get("snippet_responsibility"),
                    Jsonb(vacancy.get("raw_payload", vacancy)),
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert vacancy")
        return int(row[0])

    def _insert_salary_snapshot(self, vacancy_id: int, salary: dict[str, Any] | None) -> None:
        if not salary:
            return
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO salary_snapshots (vacancy_id, currency, salary_from, salary_to, gross)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    vacancy_id,
                    salary.get("currency"),
                    salary.get("salary_from"),
                    salary.get("salary_to"),
                    salary.get("gross"),
                ),
            )


def import_raw_file(path: Path, query: str, area_code: int | None = None) -> ImportSummary:
    config = DatabaseConfig.from_env()
    with psycopg.connect(config.dsn) as connection:
        importer = RawVacancyImporter(connection)
        return importer.import_file(path=path, query=query, area_code=area_code)
