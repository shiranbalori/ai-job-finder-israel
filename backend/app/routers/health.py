"""
Health check endpoint — use for load balancers and quick sanity checks.

GET /health
GET /api/health  (alias)
"""

from fastapi import APIRouter

from app.config import get_settings
from app.database import DATABASE_URL, engine
from app.db_utils import database_label

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/api/health")
def health_check():
    """
    Returns API status and configuration summary (no secrets).
    """
    settings = get_settings()
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    db_type = database_label(DATABASE_URL)
    db_status = f"{db_type}_connected" if db_ok else f"{db_type}_error"

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "database": db_status,
        "database_type": db_type,
        "ai_provider": settings.ai_provider,
        "mock_mode": settings.ai_provider == "mock",
        "daily_email_enabled": settings.daily_email_enabled,
    }
