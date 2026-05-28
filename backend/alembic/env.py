"""Alembic migration environment."""

from __future__ import annotations

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.db_utils import normalize_database_url, postgres_connect_args, resolve_alembic_url  # noqa: E402
from app import models  # noqa: F401,E402

logger = logging.getLogger("alembic.env")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
settings = get_settings()

# Prefer env override set by db_migrate.upgrade_to_head for multi-URL retries
migration_url = normalize_database_url(
    os.environ.get("ALEMBIC_DATABASE_URL")
    or resolve_alembic_url(settings.database_url, settings.migration_database_url)
)
config.set_main_option("sqlalchemy.url", migration_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    logger.info("[alembic] Connecting for migrations: %s", migration_url.split("@")[-1])
    connectable = create_engine(
        migration_url,
        poolclass=pool.NullPool,
        connect_args=postgres_connect_args(),
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
