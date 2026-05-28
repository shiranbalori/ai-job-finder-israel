"""Alembic migration runner — run manually via scripts/db_init.py (not on API startup)."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, pool

from app.config import get_settings
from app.db_utils import (
    migration_url_candidates,
    migration_url_host_label,
    postgres_connect_args,
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent


class MigrationTimeoutError(TimeoutError):
    """Alembic upgrade exceeded the configured time limit."""


class MigrationError(RuntimeError):
    """Alembic upgrade failed on all configured URLs."""


def get_alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def _configure_alembic_logging() -> None:
    logging.getLogger("alembic.runtime.migration").setLevel(logging.INFO)
    logging.getLogger("alembic").setLevel(logging.INFO)


def _log_pending_revisions(cfg: Config, database_url: str) -> None:
    """Log current DB revision and pending migration steps before upgrading."""
    engine = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args=postgres_connect_args(),
    )
    script = ScriptDirectory.from_config(cfg)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
            head = script.get_current_head()
            logger.info(
                "[db] Alembic state: current=%s head=%s host=%s",
                current or "(none)",
                head or "(none)",
                migration_url_host_label(database_url),
            )
            if current == head:
                logger.info("[db] Database schema is already at head — no migrations pending.")
                return

            for rev in script.iterate_revisions(head, current):
                logger.info("[db] Pending migration step: %s — %s", rev.revision, rev.doc or rev.message)
    finally:
        engine.dispose()


def _run_upgrade_once(cfg: Config, database_url: str) -> None:
    cfg.set_main_option("sqlalchemy.url", database_url)
    os.environ["ALEMBIC_DATABASE_URL"] = database_url
    _log_pending_revisions(cfg, database_url)
    logger.info("[db] Running alembic upgrade head on %s", migration_url_host_label(database_url))
    command.upgrade(cfg, "head")
    logger.info("[db] Alembic upgrade head finished on %s", migration_url_host_label(database_url))


def _run_upgrade_with_timeout(cfg: Config, database_url: str, timeout_sec: float) -> None:
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="alembic") as executor:
        future = executor.submit(_run_upgrade_once, cfg, database_url)
        try:
            future.result(timeout=timeout_sec)
        except FuturesTimeoutError as exc:
            raise MigrationTimeoutError(
                f"Alembic upgrade timed out after {timeout_sec:.0f}s on "
                f"{migration_url_host_label(database_url)}. "
                "Use Supabase session pooler (port 5432) via MIGRATION_DATABASE_URL, "
                "or run: python scripts/db_init.py"
            ) from exc


def upgrade_to_head(*, timeout_sec: float | None = None) -> None:
    """
    Apply all pending Alembic migrations.

    Tries Supabase session pooler (5432) before transaction pooler (6543).
    Raises MigrationError / MigrationTimeoutError on failure.
    """
    settings = get_settings()
    timeout = timeout_sec if timeout_sec is not None else settings.db_migration_timeout_sec
    cfg = get_alembic_config()
    _configure_alembic_logging()

    candidates = migration_url_candidates(settings.database_url, settings.migration_database_url)
    errors: list[str] = []

    for label, url in candidates:
        logger.info("[db] Migration attempt: %s (%s)", label, migration_url_host_label(url))
        try:
            _run_upgrade_with_timeout(cfg, url, timeout)
            logger.info("[db] Migrations succeeded via %s", label)
            return
        except MigrationTimeoutError:
            raise
        except Exception as exc:
            msg = f"{label} ({migration_url_host_label(url)}): {exc}"
            logger.warning("[db] Migration attempt failed — %s", msg)
            errors.append(msg)

    raise MigrationError(
        "Alembic upgrade failed on all URLs tried:\n  - " + "\n  - ".join(errors)
    )


def create_revision(message: str, autogenerate: bool = True) -> None:
    """Create a new Alembic revision (dev helper)."""
    command.revision(
        get_alembic_config(),
        message=message,
        autogenerate=autogenerate,
    )
