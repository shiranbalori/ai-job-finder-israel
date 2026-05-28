"""
CV business logic — file handling, text extraction, DB persistence.

Routers call these functions to keep HTTP layer thin and testable.
"""

import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.cv_profile import CVProfile
from app.models.user_settings import UserSettings
from app.services.cv_parser import extract_text_from_file
from app.services.cv_extraction import log_api_payload
from app.services.mock_ai import enrich_parsed_cv, mock_extract_cv
from app.services.ai_client import AIClient
from app.services.cv_parser import parse_cv_with_ai
from app.utils.json_helpers import to_json_list

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def validate_extension(filename: str) -> str:
    """Return lowercase suffix or raise ValueError."""
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".doc":
        raise ValueError(
            "Legacy .doc format is not supported. Please save as .docx or export to PDF."
        )
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF and DOCX files are supported.")
    return suffix


def validate_file_size(file_bytes: bytes) -> None:
    """Reject uploads over MAX_UPLOAD_BYTES."""
    settings = get_settings()
    if len(file_bytes) > settings.max_upload_bytes:
        mb = settings.max_upload_bytes // (1024 * 1024)
        raise ValueError(f"File too large. Maximum size is {mb} MB.")


async def save_upload_and_extract_text(file_bytes: bytes, filename: str) -> tuple[Path, str]:
    """Save uploaded bytes to disk and return (path, extracted_text)."""
    validate_file_size(file_bytes)
    suffix = validate_extension(filename)
    settings = get_settings()
    dest = settings.uploads_dir / f"{uuid.uuid4().hex}{suffix}"
    dest.write_bytes(file_bytes)
    text = extract_text_from_file(dest)
    return dest, text


def should_use_live_ai() -> bool:
    """True when AI_PROVIDER is openai/gemini (keys may still be missing — handled downstream)."""
    return get_settings().ai_provider.lower() in {"openai", "gemini"}


async def extract_cv_fields(text: str, use_live_ai: bool | None = None) -> dict:
    """
    Extract structured CV fields from plain text.

    Always runs merged heuristic skill extraction so persisted skills match
    what the parser detects — live AI hints are merged, not used alone.
    """
    import logging

    log = logging.getLogger(__name__)
    live = should_use_live_ai() if use_live_ai is None else use_live_ai

    if live:
        ai = AIClient()
        parsed = await parse_cv_with_ai(text, ai)
        log.info("[cv-extract] path=live_ai+heuristic skills=%s", parsed.get("skills", [])[:20])
        log_api_payload("cv-extract", parsed)
        return parsed

    ai = AIClient()
    if ai.is_live:
        live_result = await ai.extract_cv_profile(text)
        if live_result:
            live_result.setdefault("extraction_method", "live_ai+heuristic")
            parsed = enrich_parsed_cv(live_result, text)
            log.info("[cv-extract] path=live_ai_keys+heuristic skills=%s", parsed.get("skills", [])[:20])
            log_api_payload("cv-extract", parsed)
            return parsed

    parsed = mock_extract_cv(text)
    log.info(
        "[cv-extract] path=heuristic skills=%s confidence_count=%s",
        parsed.get("skills", [])[:20],
        len(parsed.get("skills_confidence") or []),
    )
    log_api_payload("cv-extract", parsed)
    return parsed


def persist_cv_profile(
    db: Session,
    parsed: dict,
    *,
    raw_text: str,
    filename: str | None,
    file_path: str | None = None,
    is_demo: bool = False,
    user_id: int | None = None,
) -> CVProfile:
    """Save parsed CV dict to SQLite."""
    cv = CVProfile(
        user_id=user_id,
        full_name=parsed.get("full_name"),
        email=parsed.get("email"),
        summary=parsed.get("summary"),
        years_experience=parsed.get("years_experience"),
        job_titles_json=to_json_list(parsed.get("job_titles", [])),
        skills_json=to_json_list(parsed.get("skills", [])),
        tools_json=to_json_list(parsed.get("tools", [])),
        technologies_json=to_json_list(parsed.get("technologies", [])),
        languages_json=to_json_list(parsed.get("languages", [])),
        skills_confidence_json=json.dumps(parsed.get("skills_confidence", [])),
        raw_text=raw_text[:20000],
        source_filename=filename,
        file_path=file_path,
        extraction_method=parsed.get("extraction_method", "mock_heuristic"),
        is_demo=is_demo,
        language=parsed.get("language", "en"),
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def deactivate_demo_mode(db: Session, user_id: int | None = None) -> None:
    """Switch from Demo Mode to Real Mode after a real CV upload."""
    q = db.query(UserSettings)
    if user_id is not None:
        q = q.filter(UserSettings.user_id == user_id)
    settings = q.first()
    if settings and settings.demo_mode:
        settings.demo_mode = False
        db.commit()


def get_cv_or_404(db: Session, cv_id: int) -> CVProfile:
    from fastapi import HTTPException

    cv = db.query(CVProfile).filter(CVProfile.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV profile not found.")
    return cv
