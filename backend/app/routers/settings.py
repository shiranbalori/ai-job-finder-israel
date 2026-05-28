"""
User preferences and email digest endpoints — per authenticated user.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings as get_app_settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.email_log import EmailLog
from app.models.scheduler_log import SchedulerLog
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.common import (
    EmailDigestResponse,
    EmailLogResponse,
    EmailStatusResponse,
    SchedulerLogResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.scheduler import reschedule_digest
from app.services.email_service import email_from_address, send_digest_email, smtp_configured
from app.services.user_data import get_user_settings
from app.utils.json_helpers import from_json_list, to_json_list

router = APIRouter(tags=["settings"])


def _to_response(settings: UserSettings) -> UserSettingsResponse:
    return UserSettingsResponse(
        id=settings.id,
        email=settings.email,
        daily_digest_enabled=settings.daily_digest_enabled,
        digest_hour=settings.digest_hour,
        ui_language=settings.ui_language,
        min_match_score=settings.min_match_score,
        preferred_job_keywords=from_json_list(settings.preferred_job_keywords_json),
        last_digest_sent_at=settings.last_digest_sent_at,
        demo_mode=settings.demo_mode,
        include_saved_jobs=settings.include_saved_jobs,
    )


@router.get("/api/settings", response_model=UserSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read saved preferences (email, digest, keywords, min score)."""
    return _to_response(get_user_settings(db, current_user))


@router.patch("/api/settings", response_model=UserSettingsResponse)
def patch_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update user preferences."""
    return _save_preferences(db, payload, current_user)


@router.put("/api/preferences", response_model=UserSettingsResponse)
def save_user_preferences(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save user preferences (alias for PATCH)."""
    return _save_preferences(db, payload, current_user)


def _save_preferences(
    db: Session, payload: UserSettingsUpdate, current_user: User
) -> UserSettingsResponse:
    settings = get_user_settings(db, current_user)
    data = payload.model_dump(exclude_unset=True)
    keywords = data.pop("preferred_job_keywords", None)
    if keywords is not None:
        settings.preferred_job_keywords_json = to_json_list(keywords)

    for field, value in data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    if payload.digest_hour is not None:
        reschedule_digest(settings.digest_hour)

    return _to_response(settings)


@router.get("/api/email/status", response_model=EmailStatusResponse)
def email_status():
    """Whether SMTP is configured for real sends."""
    env = get_app_settings()
    return EmailStatusResponse(
        smtp_configured=smtp_configured(),
        daily_email_enabled=env.daily_email_enabled,
        from_address=email_from_address(),
    )


@router.get("/api/email/logs", response_model=list[EmailLogResponse])
def list_email_logs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recent digest send/preview logs for the authenticated user."""
    settings = get_user_settings(db, current_user)
    rows = (
        db.query(EmailLog)
        .filter(
            or_(
                EmailLog.user_id == current_user.id,
                (EmailLog.user_id.is_(None) & (EmailLog.recipient == settings.email)),
            )
        )
        .order_by(EmailLog.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return rows


@router.get("/api/scheduler/logs", response_model=list[SchedulerLogResponse])
def list_scheduler_logs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recent scheduled digest runs for the authenticated user."""
    rows = (
        db.query(SchedulerLog)
        .filter(SchedulerLog.user_id == current_user.id)
        .order_by(SchedulerLog.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return rows


@router.post("/api/email/daily", response_model=EmailDigestResponse)
async def send_daily_email_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send or preview daily digest for the authenticated user."""
    settings = get_user_settings(db, current_user)
    if not settings.email or "@" not in settings.email:
        raise HTTPException(status_code=400, detail="Set a valid email address in settings first.")

    result = await send_digest_email(db, settings, force=True, user_id=current_user.id)
    last_sent = result.get("last_sent_at")
    return EmailDigestResponse(
        sent=bool(result.get("sent")),
        message=str(result.get("message", "")),
        count=int(result.get("count", 0)),
        preview=result.get("preview"),
        html_preview=result.get("html_preview"),
        preview_only=bool(result.get("preview_only", False)),
        last_sent_at=datetime.fromisoformat(last_sent) if isinstance(last_sent, str) else settings.last_digest_sent_at,
    )


@router.post("/api/settings/send-digest", response_model=EmailDigestResponse)
async def send_digest_legacy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy path — same as POST /api/email/daily."""
    return await send_daily_email_test(db, current_user)
