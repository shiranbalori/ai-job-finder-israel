"""Schema helpers — SQLite incremental ALTERs + cross-database data backfills."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from app.db_utils import is_sqlite_url
from app.services.job_filter import classify_job_location

logger = logging.getLogger(__name__)


def _backfill_israel_job_flags(conn: Connection) -> None:
    """Classify existing rows; demo jobs stay Israeli; deactivate non-Israel fetched jobs."""
    rows = conn.execute(text("SELECT id, location, is_demo FROM jobs")).fetchall()
    for job_id, location, is_demo in rows:
        if is_demo:
            is_israel, tag = True, classify_job_location(location or "")[1] or "israel"
        else:
            is_israel, tag = classify_job_location(location or "")
        conn.execute(
            text("UPDATE jobs SET is_israel = :is_israel, location_tag = :tag WHERE id = :id"),
            {"is_israel": is_israel, "tag": tag, "id": job_id},
        )
    conn.execute(text("UPDATE jobs SET is_active = false WHERE is_demo = false AND is_israel = false"))


def run_legacy_sqlite_migrations(engine: Engine) -> None:
    """
    SQLite-only incremental column adds for existing local databases.
    PostgreSQL schema is managed by Alembic.
    """
    if is_sqlite_url(str(engine.url)):
        _migrate_sqlite_columns(engine)

    inspector = inspect(engine)
    _migrate_auth_schema(engine, inspector)
    _backfill_legacy_user_data(engine, inspector)
    _ensure_collector_logs_table(engine, inspector)
    _migrate_log_user_columns(engine, inspector)


def _migrate_sqlite_columns(engine: Engine) -> None:
    inspector = inspect(engine)

    if "cv_profiles" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("cv_profiles")}
        cv_additions = {
            "languages_json": "ALTER TABLE cv_profiles ADD COLUMN languages_json TEXT DEFAULT '[]'",
            "extraction_method": "ALTER TABLE cv_profiles ADD COLUMN extraction_method VARCHAR(50) DEFAULT 'mock_heuristic'",
            "file_path": "ALTER TABLE cv_profiles ADD COLUMN file_path VARCHAR(500)",
            "skills_confidence_json": "ALTER TABLE cv_profiles ADD COLUMN skills_confidence_json TEXT DEFAULT '[]'",
            "embedding_json": "ALTER TABLE cv_profiles ADD COLUMN embedding_json TEXT",
            "embedding_hash": "ALTER TABLE cv_profiles ADD COLUMN embedding_hash VARCHAR(32)",
            "embedding_method": "ALTER TABLE cv_profiles ADD COLUMN embedding_method VARCHAR(40)",
            "user_id": "ALTER TABLE cv_profiles ADD COLUMN user_id INTEGER",
        }
        with engine.begin() as conn:
            for column, ddl in cv_additions.items():
                if column not in existing:
                    conn.execute(text(ddl))

    if "jobs" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("jobs")}
        job_additions = {
            "source": "ALTER TABLE jobs ADD COLUMN source VARCHAR(50) DEFAULT 'seed'",
            "external_id": "ALTER TABLE jobs ADD COLUMN external_id VARCHAR(200)",
            "work_mode": "ALTER TABLE jobs ADD COLUMN work_mode VARCHAR(50)",
            "is_israel": "ALTER TABLE jobs ADD COLUMN is_israel BOOLEAN DEFAULT 1",
            "location_tag": "ALTER TABLE jobs ADD COLUMN location_tag VARCHAR(30)",
            "parsed_skills_json": "ALTER TABLE jobs ADD COLUMN parsed_skills_json TEXT DEFAULT '[]'",
            "skills_content_hash": "ALTER TABLE jobs ADD COLUMN skills_content_hash VARCHAR(32)",
            "embedding_json": "ALTER TABLE jobs ADD COLUMN embedding_json TEXT",
            "embedding_hash": "ALTER TABLE jobs ADD COLUMN embedding_hash VARCHAR(32)",
            "embedding_method": "ALTER TABLE jobs ADD COLUMN embedding_method VARCHAR(40)",
            "tags_json": "ALTER TABLE jobs ADD COLUMN tags_json TEXT DEFAULT '[]'",
        }
        with engine.begin() as conn:
            for column, ddl in job_additions.items():
                if column not in existing:
                    conn.execute(text(ddl))
            conn.execute(text("UPDATE jobs SET source = 'seed' WHERE source IS NULL OR source = ''"))
            _backfill_israel_job_flags(conn)

    if "job_matches" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("job_matches")}
        match_additions = {
            "score_breakdown_json": "ALTER TABLE job_matches ADD COLUMN score_breakdown_json TEXT DEFAULT '{}'",
            "semantic_overlap": "ALTER TABLE job_matches ADD COLUMN semantic_overlap FLOAT DEFAULT 0",
            "semantic_matches_json": "ALTER TABLE job_matches ADD COLUMN semantic_matches_json TEXT DEFAULT '[]'",
            "job_skills_debug_json": "ALTER TABLE job_matches ADD COLUMN job_skills_debug_json TEXT DEFAULT '{}'",
            "emailed_at": "ALTER TABLE job_matches ADD COLUMN emailed_at DATETIME",
        }
        with engine.begin() as conn:
            for column, ddl in match_additions.items():
                if column not in existing:
                    conn.execute(text(ddl))

    if "user_settings" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("user_settings")}
        settings_additions = {
            "preferred_job_keywords_json": (
                "ALTER TABLE user_settings ADD COLUMN preferred_job_keywords_json TEXT DEFAULT '[]'"
            ),
            "last_digest_sent_at": "ALTER TABLE user_settings ADD COLUMN last_digest_sent_at DATETIME",
            "include_saved_jobs": "ALTER TABLE user_settings ADD COLUMN include_saved_jobs BOOLEAN DEFAULT 0",
            "user_id": "ALTER TABLE user_settings ADD COLUMN user_id INTEGER",
        }
        with engine.begin() as conn:
            for column, ddl in settings_additions.items():
                if column not in existing:
                    conn.execute(text(ddl))


def _migrate_auth_schema(engine: Engine, inspector) -> None:
    """Ensure saved_jobs has per-user uniqueness (SQLite legacy path only)."""
    if not is_sqlite_url(str(engine.url)):
        return

    tables = inspector.get_table_names()
    if "users" not in tables or "saved_jobs" not in tables:
        return

    cols = {col["name"] for col in inspector.get_columns("saved_jobs")}
    if "user_id" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE saved_jobs RENAME TO saved_jobs_legacy"))
            conn.execute(
                text(
                    """
                    CREATE TABLE saved_jobs (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        job_id INTEGER NOT NULL,
                        created_at DATETIME,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(job_id) REFERENCES jobs(id),
                        UNIQUE(user_id, job_id)
                    )
                    """
                )
            )


def _backfill_legacy_user_data(engine: Engine, inspector) -> None:
    """Assign orphan rows to a legacy user so existing data keeps working."""
    if "users" not in inspector.get_table_names():
        return

    dialect = engine.dialect.name

    with engine.begin() as conn:
        legacy = conn.execute(text("SELECT id FROM users WHERE email = 'legacy@local'")).fetchone()
        if not legacy:
            if dialect == "postgresql":
                conn.execute(
                    text(
                        """
                        INSERT INTO users (email, hashed_password, full_name, is_active, created_at)
                        VALUES ('legacy@local', :hash, 'Legacy User', true, CURRENT_TIMESTAMP)
                        """
                    ),
                    {"hash": "$2b$12$legacyplaceholderhashnotforlogin"},
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (email, hashed_password, full_name, is_active, created_at)
                        VALUES ('legacy@local', :hash, 'Legacy User', 1, datetime('now'))
                        """
                    ),
                    {"hash": "$2b$12$legacyplaceholderhashnotforlogin"},
                )
            legacy = conn.execute(text("SELECT id FROM users WHERE email = 'legacy@local'")).fetchone()

        if not legacy:
            return

        legacy_id = legacy[0]
        conn.execute(
            text("UPDATE cv_profiles SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": legacy_id},
        )
        conn.execute(
            text("UPDATE user_settings SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": legacy_id},
        )

        if "saved_jobs_legacy" in inspector.get_table_names():
            rows = conn.execute(text("SELECT job_id, created_at FROM saved_jobs_legacy")).fetchall()
            for job_id, created_at in rows:
                if dialect == "postgresql":
                    conn.execute(
                        text(
                            """
                            INSERT INTO saved_jobs (user_id, job_id, created_at)
                            VALUES (:uid, :job_id, :created_at)
                            ON CONFLICT (user_id, job_id) DO NOTHING
                            """
                        ),
                        {"uid": legacy_id, "job_id": job_id, "created_at": created_at},
                    )
                else:
                    conn.execute(
                        text(
                            """
                            INSERT OR IGNORE INTO saved_jobs (user_id, job_id, created_at)
                            VALUES (:uid, :job_id, :created_at)
                            """
                        ),
                        {"uid": legacy_id, "job_id": job_id, "created_at": created_at},
                    )
            conn.execute(text("DROP TABLE saved_jobs_legacy"))


def _ensure_collector_logs_table(engine: Engine, inspector) -> None:
    if "job_collector_logs" in inspector.get_table_names():
        return

    if is_sqlite_url(str(engine.url)):
        ddl = """
            CREATE TABLE job_collector_logs (
                id INTEGER PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'started',
                sources_json TEXT DEFAULT '[]',
                total_fetched INTEGER DEFAULT 0,
                total_matched INTEGER DEFAULT 0,
                total_created INTEGER DEFAULT 0,
                total_updated INTEGER DEFAULT 0,
                total_skipped INTEGER DEFAULT 0,
                duration_ms INTEGER,
                errors_json TEXT DEFAULT '[]',
                message TEXT DEFAULT '',
                created_at DATETIME DEFAULT (datetime('now'))
            )
        """
    else:
        ddl = """
            CREATE TABLE job_collector_logs (
                id SERIAL PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'started',
                sources_json TEXT DEFAULT '[]',
                total_fetched INTEGER DEFAULT 0,
                total_matched INTEGER DEFAULT 0,
                total_created INTEGER DEFAULT 0,
                total_updated INTEGER DEFAULT 0,
                total_skipped INTEGER DEFAULT 0,
                duration_ms INTEGER,
                errors_json TEXT DEFAULT '[]',
                message TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

    with engine.begin() as conn:
        conn.execute(text(ddl))


def _migrate_log_user_columns(engine: Engine, inspector) -> None:
    """Add user_id to email_logs / scheduler_logs for per-user digest audit."""
    tables = inspector.get_table_names()
    with engine.begin() as conn:
        if "email_logs" in tables:
            cols = {col["name"] for col in inspector.get_columns("email_logs")}
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE email_logs ADD COLUMN user_id INTEGER"))
        if "scheduler_logs" in tables:
            cols = {col["name"] for col in inspector.get_columns("scheduler_logs")}
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE scheduler_logs ADD COLUMN user_id INTEGER"))
