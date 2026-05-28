"""
Database setup with SQLAlchemy ORM.

Local development: SQLite (backend/data/app.db)
Production: PostgreSQL via Supabase (DATABASE_URL)
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.config import get_settings
from app.db_utils import is_postgres_url, is_sqlite_url, normalize_database_url, postgres_connect_args

logger = logging.getLogger(__name__)
settings = get_settings()
DATABASE_URL = normalize_database_url(settings.database_url)


def _build_engine():
    url = DATABASE_URL

    if is_sqlite_url(url):
        connect_args = {"check_same_thread": False}
        if url.endswith(":memory:") or url.rstrip("/").endswith("sqlite://"):
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(url, connect_args=connect_args)

    if is_postgres_url(url):
        engine_kwargs: dict = {
            "pool_pre_ping": True,
            "connect_args": postgres_connect_args(),
        }
        # Supabase transaction pooler (port 6543) — avoid client-side pooling
        if settings.db_use_null_pool or ":6543" in url:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = settings.db_pool_size
            engine_kwargs["max_overflow"] = settings.db_max_overflow
        return create_engine(url, **engine_kwargs)

    return create_engine(url)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if not is_sqlite_url(DATABASE_URL):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def get_db():
    """
    FastAPI dependency: yields a DB session and closes it after the request.
    Usage: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Prepare database for the active backend — SQLite only creates schema on startup."""
    from app import models  # noqa: F401 — register ORM models with Base
    from app.migrations import run_legacy_sqlite_migrations

    if is_sqlite_url(DATABASE_URL):
        Base.metadata.create_all(bind=engine)
        run_legacy_sqlite_migrations(engine)
        return

    if settings.db_run_migrations_on_startup:
        from app.db_migrate import upgrade_to_head

        logger.warning(
            "DB_RUN_MIGRATIONS_ON_STARTUP=true — running Alembic on startup (can block/hang on Supabase pooler)"
        )
        upgrade_to_head()
    else:
        logger.info(
            "PostgreSQL connected — skipping Alembic on startup. "
            "Apply schema with: python scripts/db_init.py"
        )

    run_legacy_sqlite_migrations(engine)
