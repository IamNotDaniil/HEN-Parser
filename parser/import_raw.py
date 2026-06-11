from __future__ import annotations

import argparse
from pathlib import Path

from parser.db import import_raw_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a raw hh.ru JSON export into PostgreSQL.")
    parser.add_argument("path", type=Path, help="Path to JSON file from data/raw")
    parser.add_argument("--query", required=True, help="Search query used to fetch the raw export")
    parser.add_argument("--area", type=int, default=None, help="hh.ru area id used for the raw export")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = import_raw_file(path=args.path, query=args.query, area_code=args.area)
    print(f"Source run: {summary.run_id}")
    print(f"Fetched records: {summary.fetched_count}")
    print(f"Imported records: {summary.imported_count}")


if __name__ == "__main__":
    main()
