from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import requests

from parser.hh_client import HHClient
from parser.storage import RawDataWriter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch vacancies from hh.ru and save raw exports.")
    parser.add_argument("query", help="Search query, e.g. Python or Go")
    parser.add_argument("--area", type=int, default=None, help="hh.ru area id")
    parser.add_argument("--pages", type=int, default=1, help="How many result pages to fetch")
    parser.add_argument("--per-page", type=int, default=20, help="Vacancies per page")
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory where JSON and CSV exports will be written",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client = HHClient()
    try:
        vacancies = client.iter_vacancies(
            query=args.query,
            area=args.area,
            max_pages=args.pages,
            per_page=args.per_page,
        )
    except requests.RequestException as error:
        raise SystemExit(f"Failed to fetch vacancies from hh.ru: {error}") from error

    writer = RawDataWriter(output_dir=args.output_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_query = "_".join(args.query.lower().split())
    prefix = f"hh_{safe_query}_{timestamp}"

    json_path = writer.write_json(f"{prefix}.json", vacancies)
    csv_path = writer.write_csv(f"{prefix}.csv", vacancies)

    print(f"Fetched {len(vacancies)} vacancies")
    print(f"JSON export: {Path(json_path)}")
    print(f"CSV export: {Path(csv_path)}")


if __name__ == "__main__":
    main()
