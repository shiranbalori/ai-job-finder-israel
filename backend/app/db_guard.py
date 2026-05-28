"""Production environment safety checks."""

from __future__ import annotations

from app.db_utils import database_label, is_sqlite_url

_JWT_PLACEHOLDERS = frozenset(
    {
        "change-me-in-production-use-long-random-string",
        "replace-with-long-random-string",
    }
)


class DatabaseConfigError(Exception):
    """Invalid database configuration for the active environment."""


class ProductionConfigError(Exception):
    """Invalid production configuration (secrets, CORS, etc.)."""


def validate_production_database(app_env: str, database_url: str) -> None:
    """
    Refuse production startup when DATABASE_URL points at SQLite.

    Local development (APP_ENV=development + SQLite) is always allowed.
    """
    if app_env.lower() != "production":
        return

    if is_sqlite_url(database_url):
        raise DatabaseConfigError(
            "APP_ENV=production cannot use SQLite.\n"
            "Set DATABASE_URL to your Supabase PostgreSQL URI on the hosting provider "
            "(Render env vars). See README.md § Supabase setup and docs/DEPLOYMENT.md."
        )

    if database_label(database_url) != "postgresql":
        raise DatabaseConfigError(
            f"APP_ENV=production requires PostgreSQL; got {database_label(database_url)!r}."
        )


def validate_production_secrets(
    app_env: str,
    jwt_secret: str,
    cors_origins: str,
    cors_origin_regex: str = "",
) -> None:
    """Refuse production startup with placeholder JWT or missing CORS config."""
    if app_env.lower() != "production":
        return

    secret = (jwt_secret or "").strip()
    if not secret or secret in _JWT_PLACEHOLDERS or len(secret) < 32:
        raise ProductionConfigError(
            "JWT_SECRET must be a random string of at least 32 characters in production."
        )

    origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    if not origins and not (cors_origin_regex or "").strip():
        raise ProductionConfigError(
            "Set CORS_ORIGINS and/or CORS_ORIGIN_REGEX so the Vercel frontend can call the API."
        )
