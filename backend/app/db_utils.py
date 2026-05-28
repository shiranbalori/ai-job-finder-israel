"""Database URL helpers — SQLite (local) and PostgreSQL (Supabase production)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

DEFAULT_PG_CONNECT_TIMEOUT_SEC = 15


def normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy 2.

    - postgres:// → postgresql+psycopg2://
    - postgresql:// → postgresql+psycopg2://
    - Ensures sslmode=require and connect_timeout for Supabase hosts when missing
    """
    raw = (url or "").strip()
    if not raw:
        return "sqlite:///./data/app.db"

    if raw.startswith("postgres://"):
        raw = "postgresql+psycopg2://" + raw[len("postgres://") :]
    elif raw.startswith("postgresql://") and "+psycopg" not in raw:
        raw = "postgresql+psycopg2://" + raw[len("postgresql://") :]

    if is_postgres_url(raw):
        if _is_supabase_host(raw) and "sslmode=" not in raw.lower():
            raw = _append_query_param(raw, "sslmode", "require")
        if "connect_timeout=" not in raw.lower():
            raw = _append_query_param(raw, "connect_timeout", str(DEFAULT_PG_CONNECT_TIMEOUT_SEC))

    return raw


def postgres_connect_args() -> dict:
    """psycopg2 connect_args — backup if URL query params are stripped."""
    return {"connect_timeout": DEFAULT_PG_CONNECT_TIMEOUT_SEC}


def is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite:")


def is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql")


def database_label(url: str) -> str:
    if is_sqlite_url(url):
        return "sqlite"
    if is_postgres_url(url):
        return "postgresql"
    return "unknown"


def migration_url_host_label(url: str) -> str:
    """Safe host:port for logs — never includes credentials."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "?"
        port = parsed.port or ("5432" if is_postgres_url(url) else "")
        return f"{host}:{port}" if port else host
    except Exception:
        return "unknown"


def supabase_session_pooler_url(url: str) -> str:
    """
    Prefer Supabase session pooler (port 5432) for DDL/migrations.

    Transaction pooler (6543) can hang on Alembic; session pooler on the same host is safer.
    """
    normalized = normalize_database_url(url)
    if not is_postgres_url(normalized):
        return normalized

    parsed = urlparse(normalized)
    host = parsed.hostname or ""
    if not host.endswith(".pooler.supabase.com"):
        return normalized

    port = parsed.port
    if port == 6543:
        netloc = parsed.netloc.rsplit(":", 1)[0] + ":5432"
        normalized = urlunparse(parsed._replace(netloc=netloc))
    return normalize_database_url(normalized)


def resolve_alembic_url(database_url: str, migration_database_url: str = "") -> str:
    """URL for Alembic — explicit override, else session pooler, else DATABASE_URL."""
    if migration_database_url.strip():
        return normalize_database_url(migration_database_url)
    base = normalize_database_url(database_url)
    if is_postgres_url(base):
        return supabase_session_pooler_url(base)
    return base


def migration_url_candidates(database_url: str, migration_database_url: str = "") -> list[tuple[str, str]]:
    """Ordered migration URLs to try (session pooler before transaction pooler)."""
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(label: str, url: str) -> None:
        normalized = normalize_database_url(url)
        if normalized in seen:
            return
        seen.add(normalized)
        candidates.append((label, normalized))

    if migration_database_url.strip():
        add("MIGRATION_DATABASE_URL", migration_database_url)

    base = normalize_database_url(database_url)
    session = supabase_session_pooler_url(base)
    if session != base:
        add("Supabase session pooler (port 5432)", session)
    add("DATABASE_URL", base)
    return candidates


def _is_supabase_host(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    return host.endswith(".supabase.co") or host.endswith(".pooler.supabase.com")


def _append_query_param(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if key not in query:
        query[key] = [value]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
