#!/usr/bin/env python3
"""
Copy data from a local SQLite database to PostgreSQL (Supabase).

Usage (from backend/):
  python scripts/sqlite_to_postgres.py --source ./data/app.db

Requires DATABASE_URL in .env to point at the target PostgreSQL database.
Schema must already exist (run: python scripts/db_upgrade.py first).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db_utils import normalize_database_url

TABLE_ORDER = [
    "users",
    "jobs",
    "cv_profiles",
    "user_settings",
    "job_matches",
    "saved_jobs",
    "email_logs",
    "scheduler_logs",
]


def copy_table(src_conn, dst_conn, table: str) -> int:
    inspector = inspect(src_conn)
    if table not in inspector.get_table_names():
        return 0

    columns = [c["name"] for c in inspector.get_columns(table)]
    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)

    rows = src_conn.execute(text(f"SELECT {col_list} FROM {table}")).mappings().all()
    if not rows:
        return 0

    for row in rows:
        dst_conn.execute(
            text(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"),
            dict(row),
        )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL")
    parser.add_argument(
        "--source",
        default=str(BACKEND_DIR / "data" / "app.db"),
        help="Path to SQLite app.db file",
    )
    args = parser.parse_args()

    settings = get_settings()
    target_url = normalize_database_url(settings.database_url)
    if not target_url.startswith("postgresql"):
        print("ERROR: DATABASE_URL must be PostgreSQL. Set it in backend/.env")
        sys.exit(1)

    source_path = Path(args.source)
    if not source_path.is_file():
        print(f"ERROR: SQLite file not found: {source_path}")
        sys.exit(1)

    src_engine = create_engine(f"sqlite:///{source_path.resolve()}")
    dst_engine = create_engine(target_url, pool_pre_ping=True)

    print(f"Source: {source_path}")
    print(f"Target: {target_url.split('@')[-1] if '@' in target_url else target_url}")

    with src_engine.connect() as src_conn, dst_engine.begin() as dst_conn:
        for table in reversed(TABLE_ORDER):
            inspector = inspect(dst_conn)
            if table in inspector.get_table_names():
                dst_conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))

        total = 0
        for table in TABLE_ORDER:
            count = copy_table(src_conn, dst_conn, table)
            print(f"  {table}: {count} rows")
            total += count

    print(f"Done — {total} rows copied.")


if __name__ == "__main__":
    main()
