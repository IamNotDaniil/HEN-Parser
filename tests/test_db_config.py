from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from parser.db import DatabaseConfig


class DatabaseConfigTest(unittest.TestCase):
    def test_database_url_has_priority(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://example"}, clear=True):
            self.assertEqual(DatabaseConfig.from_env().dsn, "postgresql://example")

    def test_builds_dsn_from_postgres_environment(self) -> None:
        env = {
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "jobs",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                DatabaseConfig.from_env().dsn,
                "host=db port=5433 dbname=jobs user=user password=secret",
            )


if __name__ == "__main__":
    unittest.main()
