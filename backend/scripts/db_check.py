#!/usr/bin/env python3
"""
Test the configured database connection.

Run from backend/:

    python scripts/db_check.py

Works with local SQLite and production Supabase PostgreSQL.
Exits with code 1 if APP_ENV=production is paired with SQLite.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text

from app.config import get_settings
from app.db_guard import DatabaseConfigError
from app.db_utils import database_label, is_sqlite_url

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    try:
        settings = get_settings()
    except DatabaseConfigError as exc:
        print(f"Configuration error: {exc}")
        return 1

    from app.database import DATABASE_URL, engine

    db_type = database_label(DATABASE_URL)

    logger.info("APP_ENV: %s", settings.app_env)
    logger.info("Database type: %s", db_type)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"Connection failed ({db_type}): {exc}")
        return 1

    if is_sqlite_url(DATABASE_URL):
        print("Database connection OK (SQLite — local development).")
    else:
        print("Database connection OK (PostgreSQL — Supabase/production).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
