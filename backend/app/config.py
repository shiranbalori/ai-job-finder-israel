"""Application configuration loaded from environment variables."""

import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db_guard import validate_production_database, validate_production_secrets
from app.db_utils import database_label, normalize_database_url, resolve_alembic_url

logger = logging.getLogger(__name__)

# backend/app/config.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_BACKEND = BASE_DIR / ".env"
ENV_ROOT = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Prefer backend/.env (where run.py lives); fall back to repo-root .env
        env_file=tuple(
            str(p) for p in (ENV_BACKEND, ENV_ROOT) if p.is_file()
        ) or (str(ENV_BACKEND),),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Job Finder Israel"
    app_env: str = "development"  # development | production
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000  # Render sets PORT; see _resolve_port below
    database_url: str = "sqlite:///./data/app.db"
    migration_database_url: str = ""  # optional direct Supabase URL (port 5432) for Alembic
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_use_null_pool: bool = False  # true for Supabase transaction pooler (port 6543)
    db_run_migrations_on_startup: bool = False  # false — run python scripts/db_init.py instead
    db_migration_timeout_sec: float = 120.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str = ""  # e.g. https://.*\.vercel\.app for Vercel previews

    ai_provider: str = "mock"  # openai | gemini | mock
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    use_embeddings: bool = True

    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@aijobfinder.co.il"
    smtp_use_tls: bool = True

    # Alias supported in .env
    email_from: str = ""

    daily_email_enabled: bool = False
    daily_email_hour: int = 8
    daily_email_recipient: str = "demo@example.com"

    demo_mode_default: bool = False
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Job board adapters (comma-separated)
    greenhouse_board_tokens: str = ""
    lever_company_slugs: str = ""
    job_fetch_on_startup: bool = True
    job_refresh_enabled: bool = True
    job_refresh_interval_hours: int = 4
    job_collector_timeout_sec: float = 120.0

    @field_validator("database_url", "migration_database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: object) -> str:
        raw = str(value or "").strip()
        if not raw:
            return raw
        return normalize_database_url(raw)

    @property
    def effective_migration_url(self) -> str:
        """URL used by Alembic — session pooler (5432) when available."""
        return resolve_alembic_url(self.database_url, self.migration_database_url)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def effective_smtp_from(self) -> str:
        return self.email_from or self.smtp_from

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def uploads_dir(self) -> Path:
        path = BASE_DIR / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_dir(self) -> Path:
        path = BASE_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    validate_production_database(settings.app_env, settings.database_url)
    validate_production_secrets(
        settings.app_env,
        settings.jwt_secret,
        settings.cors_origins,
        settings.cors_origin_regex,
    )
    return settings


def _secret_loaded(value: str, *, placeholders: frozenset[str] = frozenset()) -> bool:
    return bool(value and value.strip() and value.strip() not in placeholders)


def log_db_startup() -> None:
    """Safe startup log — database type and pool mode only, never prints secrets."""
    s = get_settings()
    db_type = database_label(s.database_url)
    null_pool = s.db_use_null_pool or (":6543" in s.database_url)
    logger.info("APP_ENV: %s", s.app_env)
    logger.info("Database type: %s", db_type)
    logger.info("DB_USE_NULL_POOL: %s", "yes" if null_pool else "no")
    logger.info("CORS origins: %s", len(s.cors_origin_list))
    if s.cors_origin_regex.strip():
        logger.info("CORS origin regex: configured")
    if s.migration_database_url:
        logger.info("MIGRATION_DATABASE_URL: configured (%s)", database_label(s.migration_database_url))
    if db_type == "sqlite":
        logger.info("Local SQLite — tables created on startup via init_db() (no Alembic needed).")
    else:
        logger.info(
            "PostgreSQL — Alembic skipped on startup (DB_RUN_MIGRATIONS_ON_STARTUP=%s). "
            "Run migrations manually: python scripts/db_init.py",
            "true" if s.db_run_migrations_on_startup else "false",
        )


def log_smtp_startup() -> None:
    """Safe startup log — yes/no only, never prints secrets."""
    env_sources = [p for p in (ENV_BACKEND, ENV_ROOT) if p.is_file()]
    logger.info(
        "Env files: %s",
        ", ".join(str(p) for p in env_sources) if env_sources else "(none found — using process env only)",
    )
    s = get_settings()
    host_ok = _secret_loaded(s.smtp_host, placeholders=frozenset({"smtp.example.com", "localhost"}))
    user_ok = _secret_loaded(s.smtp_user)
    password_ok = _secret_loaded(s.smtp_password)
    from_ok = _secret_loaded(s.effective_smtp_from)
    smtp_ready = host_ok and user_ok and password_ok

    logger.info("SMTP_HOST loaded: %s", "yes" if host_ok else "no")
    logger.info("SMTP_USER loaded: %s", "yes" if user_ok else "no")
    logger.info("SMTP_PASSWORD loaded: %s", "yes" if password_ok else "no")
    logger.info("EMAIL_FROM loaded: %s", "yes" if from_ok else "no")
    logger.info("SMTP ready for real send: %s", "yes" if smtp_ready else "no")
    if not smtp_ready:
        logger.info(
            "Email will stay in preview mode until SMTP_HOST, SMTP_USER, and SMTP_PASSWORD are set in backend/.env"
        )
