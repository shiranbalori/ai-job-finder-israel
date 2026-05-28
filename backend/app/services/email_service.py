"""
Daily email digest — SMTP sender with HTML template, logging, and demo-safe preview.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user_settings import UserSettings
from app.services.digest_service import prepare_digest_matches, _log_email
from app.services.email_template import render_digest_html, render_digest_plain
from app.utils.serializers import match_to_response

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    s = get_settings()
    return bool(
        s.smtp_host
        and s.smtp_host not in {"smtp.example.com", "localhost"}
        and s.smtp_user
        and s.smtp_password
    )


def email_from_address() -> str:
    s = get_settings()
    return s.effective_smtp_from or s.smtp_user or "noreply@aijobfinder.co.il"


async def send_digest_email(
    db: Session,
    user_settings: UserSettings,
    *,
    force: bool = False,
    refresh_jobs: bool | None = None,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Run full digest pipeline and send (or preview) email.

    Demo Mode → HTML preview only, never sends.
    force=True → manual test from Settings (still respects demo_mode).
    """
    env = get_settings()
    recipient = user_settings.email
    subject = "Your daily AI job matches — Israel"
    smtp_ready = smtp_configured()
    preview_only = user_settings.demo_mode or not smtp_ready
    log_user_id = user_id if user_id is not None else user_settings.user_id

    if not force and not user_settings.daily_digest_enabled:
        return {
            "sent": False,
            "message": "Daily digest is disabled in settings.",
            "count": 0,
            "preview_only": True,
        }

    if not env.daily_email_enabled and not force:
        logger.info("[email] DAILY_EMAIL_ENABLED=false — scheduler gate closed")
        return {
            "sent": False,
            "message": "Email automation disabled via DAILY_EMAIL_ENABLED env.",
            "count": 0,
            "preview_only": True,
        }

    matches, cv = await prepare_digest_matches(
        db,
        user_settings,
        include_emailed=force,
        refresh_jobs=refresh_jobs if refresh_jobs is not None else not force,
    )
    if not cv:
        msg = (
            "Upload a real CV first to receive matches."
            if not user_settings.demo_mode
            else "Upload a CV first to receive matches."
        )
        return {"sent": False, "message": msg, "count": 0, "preview_only": preview_only}

    if not matches:
        reason = "No new qualifying matches to email."
        if not user_settings.demo_mode and cv.is_demo:
            reason = "Only demo CV found — upload a real CV for live email digests."
        _log_email(
            db,
            user_id=log_user_id,
            recipient=recipient,
            subject=subject,
            match_count=0,
            sent=False,
            preview_only=True,
            error=None,
            job_ids=[],
        )
        db.commit()
        return {"sent": False, "message": reason, "count": 0, "preview_only": preview_only}

    payload = [match_to_response(m, include_job=True).model_dump() for m in matches]
    html_body = render_digest_html(
        payload,
        recipient=recipient,
        min_score=user_settings.min_match_score,
        language=user_settings.ui_language,
    )
    plain_body = render_digest_plain(payload, min_score=user_settings.min_match_score)

    if preview_only:
        if user_settings.demo_mode:
            preview_msg = "Demo mode — email preview generated. No email was sent."
        elif not smtp_ready:
            preview_msg = "SMTP is not configured — email preview generated. No email was sent."
        else:
            preview_msg = "Preview mode — email generated but not sent."
        logger.info(
            "[email] PREVIEW ONLY (demo=%s smtp=%s) recipient=%s matches=%s",
            user_settings.demo_mode,
            smtp_ready,
            recipient,
            len(matches),
        )
        _log_email(
            db,
            user_id=log_user_id,
            recipient=recipient,
            subject=subject,
            match_count=len(matches),
            sent=False,
            preview_only=True,
            error=None,
            job_ids=[m.job_id for m in matches],
        )
        user_settings.last_digest_sent_at = datetime.utcnow()
        db.commit()
        return {
            "sent": False,
            "message": preview_msg,
            "count": len(matches),
            "preview": plain_body,
            "html_preview": html_body,
            "preview_only": True,
            "last_sent_at": user_settings.last_digest_sent_at.isoformat(),
        }

    try:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = email_from_address()
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(plain_body)
        msg.add_alternative(html_body, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=env.smtp_host,
            port=env.smtp_port,
            username=env.smtp_user,
            password=env.smtp_password,
            start_tls=env.smtp_use_tls,
        )

        now = datetime.utcnow()
        for m in matches:
            m.emailed_at = now
        user_settings.last_digest_sent_at = now
        _log_email(
            db,
            user_id=log_user_id,
            recipient=recipient,
            subject=subject,
            match_count=len(matches),
            sent=True,
            preview_only=False,
            error=None,
            job_ids=[m.job_id for m in matches],
        )
        db.commit()
        logger.info("[email] sent digest to %s (%s jobs)", recipient, len(matches))
        return {
            "sent": True,
            "message": f"Email sent successfully to {recipient}.",
            "count": len(matches),
            "preview_only": False,
            "last_sent_at": now.isoformat(),
        }
    except Exception as exc:
        logger.exception("[email] SMTP send failed")
        err_msg = f"Failed to send email: {exc}"
        _log_email(
            db,
            user_id=log_user_id,
            recipient=recipient,
            subject=subject,
            match_count=len(matches),
            sent=False,
            preview_only=False,
            error=str(exc)[:500],
            job_ids=[m.job_id for m in matches],
        )
        db.commit()
        return {
            "sent": False,
            "message": err_msg,
            "count": len(matches),
            "preview": plain_body,
            "html_preview": html_body,
            "preview_only": False,
        }
