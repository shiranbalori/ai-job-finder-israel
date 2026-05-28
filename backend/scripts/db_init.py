#!/usr/bin/env python3
"""
Initialize PostgreSQL tables (Alembic migrations → latest schema).

Run from backend/ with Supabase env vars in backend/.env:

    python scripts/db_init.py

Alembic is NOT run on API startup (avoids Supabase pooler hangs).
Uses session pooler (port 5432) automatically when DATABASE_URL uses port 6543.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings
from app.db_guard import DatabaseConfigError, validate_production_database
from app.db_migrate import MigrationError, MigrationTimeoutError, upgrade_to_head
from app.db_utils import database_label, is_sqlite_url, migration_url_host_label, resolve_alembic_url

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    try:
        settings = get_settings()
    except DatabaseConfigError as exc:
        print(f"FAIL — configuration error: {exc}")
        return 1

    migration_url = resolve_alembic_url(settings.database_url, settings.migration_database_url)
    db_type = database_label(migration_url)

    try:
        validate_production_database(settings.app_env, settings.database_url)
    except DatabaseConfigError as exc:
        print(f"FAIL — configuration error: {exc}")
        return 1

    if is_sqlite_url(migration_url):
        print(
            "FAIL — SQLite detected. This script initializes PostgreSQL/Supabase only.\n"
            "Local dev: keep DATABASE_URL=sqlite:///./data/app.db and run python run.py.\n"
            "Supabase: set DATABASE_URL in backend/.env, then run this script again."
        )
        return 1

    logger.info("Initializing %s schema (timeout=%ss)...", db_type, settings.db_migration_timeout_sec)
    logger.info("Primary migration host: %s", migration_url_host_label(migration_url))
    if settings.migration_database_url:
        logger.info("MIGRATION_DATABASE_URL override is set.")
    elif ":6543" in settings.database_url:
        logger.info("DATABASE_URL uses transaction pooler (6543) — will try session pooler (5432) first.")

    try:
        upgrade_to_head(timeout_sec=settings.db_migration_timeout_sec)
    except MigrationTimeoutError as exc:
        print(f"FAIL — migration timed out: {exc}")
        return 1
    except MigrationError as exc:
        print(f"FAIL — migration error: {exc}")
        return 1

    print("SUCCESS — PostgreSQL tables initialized (alembic upgrade head).")
    print("Next: python scripts/db_check.py && python run.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
