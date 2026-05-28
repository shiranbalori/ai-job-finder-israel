"""
CV endpoints — upload, extract, and retrieve profiles.
"""

import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import (
    CVExtractResponse,
    CVInsightsResponse,
    CVProfileResponse,
    CVUploadResponse,
    ExtractionDebug,
    SkillConfidence,
)
from app.services.cv_insights_service import build_cv_insights
from app.services.cv_service import (
    deactivate_demo_mode,
    extract_cv_fields,
    get_cv_or_404,
    persist_cv_profile,
    save_upload_and_extract_text,
)
from app.services.job_availability import ensure_jobs_for_matching
from app.services.job_matcher import DEFAULT_JOB_LIMIT, UPLOAD_MATCH_TIMEOUT_SEC
from app.services.match_service import calculate_matches
from app.services.user_data import get_cv_for_user, get_user_latest_cv
from app.utils.serializers import cv_to_response, match_to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cv", tags=["cv"])

UPLOAD_TOP_MATCHES = 10


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(..., description="PDF or DOCX resume"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload CV → extract skills → match top Israeli jobs → return results."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    upload_t0 = time.perf_counter()
    logger.info("[UPLOAD_START] filename=%s user_id=%s", file.filename, current_user.id)

    try:
        t_file = time.perf_counter()
        content = await file.read()
        saved_path, text = await save_upload_and_extract_text(content, file.filename)
        logger.info(
            "[TEXT_EXTRACT_DONE] ms=%s text_len=%s",
            int((time.perf_counter() - t_file) * 1000),
            len(text),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}") from exc

    t_skills = time.perf_counter()
    parsed = await extract_cv_fields(text)
    logger.info(
        "[SKILL_EXTRACT_DONE] ms=%s skills=%s method=%s",
        int((time.perf_counter() - t_skills) * 1000),
        len(parsed.get("skills") or []),
        parsed.get("extraction_method"),
    )

    t_db = time.perf_counter()
    cv = persist_cv_profile(
        db,
        parsed,
        raw_text=text,
        filename=file.filename,
        file_path=str(saved_path),
        is_demo=False,
        user_id=current_user.id,
    )
    deactivate_demo_mode(db, user_id=current_user.id)
    logger.info("[DB_SAVE_DONE] ms=%s cv_profile_id=%s", int((time.perf_counter() - t_db) * 1000), cv.id)

    t_jobs = time.perf_counter()
    jobs_count = await ensure_jobs_for_matching(db, min_jobs=1, israel_only=True)
    logger.info(
        "[JOB_LOAD_DONE] jobs_count=%s limit=%s ms=%s",
        jobs_count,
        DEFAULT_JOB_LIMIT,
        int((time.perf_counter() - t_jobs) * 1000),
    )

    t_match = time.perf_counter()
    match_result = await calculate_matches(
        db,
        cv,
        min_score=0,
        israel_only=True,
        job_limit=DEFAULT_JOB_LIMIT,
        quiet=True,
        fast=True,
        use_embeddings=False,
        match_timeout_sec=UPLOAD_MATCH_TIMEOUT_SEC,
    )
    match_rows = match_result.matches[:UPLOAD_TOP_MATCHES]
    top_score = match_rows[0].match_score if match_rows else None
    logger.info(
        "[MATCHING_DONE] cv_profile_id=%s jobs_count=%s matches_created=%s top_score=%s ms=%s partial=%s",
        cv.id,
        match_result.jobs_total,
        len(match_result.matches),
        top_score,
        int((time.perf_counter() - t_match) * 1000),
        match_result.partial,
    )

    method = parsed.get("extraction_method", "mock_heuristic")
    skills_confidence = parsed.get("skills_confidence", [])
    debug_raw = parsed.get("extraction_debug") or {}
    extraction_debug = ExtractionDebug(**debug_raw) if debug_raw else None

    base_message = (
        f"CV uploaded — {len(match_result.matches)} matches from "
        f"{match_result.jobs_scored}/{match_result.jobs_total} Israeli jobs ({method})."
    )
    if not match_result.matches:
        base_message = (
            f"CV uploaded — skills extracted, but no job matches were found "
            f"({match_result.jobs_total} jobs checked). Try refreshing jobs from the dashboard."
        )
    if match_result.warning:
        base_message = f"{base_message} {match_result.warning}"

    response = CVUploadResponse(
        cv_profile=cv_to_response(cv),
        matches=[match_to_response(m) for m in match_rows],
        total_jobs_scored=match_result.jobs_scored,
        extraction_method=method,
        skills_confidence=skills_confidence,
        extraction_debug=extraction_debug,
        raw_text_preview=text[:800],
        message=base_message,
        partial_matches=match_result.partial,
        match_warning=match_result.warning,
        jobs_count=match_result.jobs_total,
        matches_created=len(match_result.matches),
        top_score=top_score,
    )

    total_ms = int((time.perf_counter() - upload_t0) * 1000)
    logger.info(
        "[UPLOAD_DONE] total_ms=%s cv_profile_id=%s jobs_count=%s matches_created=%s top_score=%s returned=%s",
        total_ms,
        cv.id,
        match_result.jobs_total,
        len(match_result.matches),
        top_score,
        len(match_rows),
    )
    return response


@router.post("/extract", response_model=CVExtractResponse)
async def extract_cv_information(
    file: UploadFile | None = File(None, description="PDF or DOCX to parse"),
    raw_text: str | None = Form(None, description="Plain text alternative to file upload"),
    save: bool = Form(False, description="If true, persist profile to SQLite"),
    db: Session = Depends(get_db),
):
    """Extract CV information — returns structured fields without mandatory DB save."""
    if not file and not raw_text:
        raise HTTPException(status_code=400, detail="Provide either file or raw_text.")

    text = raw_text or ""
    filename = None
    file_path = None

    if file:
        try:
            content = await file.read()
            saved_path, text = await save_upload_and_extract_text(content, file.filename or "cv.pdf")
            filename = file.filename
            file_path = str(saved_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    parsed = await extract_cv_fields(text)

    debug_raw = parsed.get("extraction_debug") or {}
    extraction_debug = ExtractionDebug(**debug_raw) if debug_raw else None

    if save:
        cv = persist_cv_profile(
            db,
            parsed,
            raw_text=text,
            filename=filename,
            file_path=file_path,
            is_demo=False,
        )
        deactivate_demo_mode(db)
        return CVExtractResponse(
            **cv_to_response(cv).model_dump(),
            extraction_method=parsed.get("extraction_method", "mock_heuristic"),
            extraction_debug=extraction_debug,
            raw_text_preview=text[:500],
        )

    return CVExtractResponse(
        **parsed,
        extraction_debug=extraction_debug,
        raw_text_preview=text[:500],
    )


@router.get("/latest", response_model=CVProfileResponse | None)
def get_latest_cv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's most recently uploaded CV."""
    cv = get_user_latest_cv(db, current_user)
    return cv_to_response(cv) if cv else None


@router.get("/insights", response_model=CVInsightsResponse)
def get_cv_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cv_profile_id: int | None = None,
    israel_only: bool = True,
):
    """Aggregated CV insights — skills, gaps, learning areas, career tips."""
    if cv_profile_id:
        get_cv_for_user(db, current_user, cv_profile_id)
    else:
        cv = get_user_latest_cv(db, current_user)
        cv_profile_id = cv.id if cv else None
    return build_cv_insights(db, cv_profile_id, israel_only=israel_only)


@router.get("/{cv_id}", response_model=CVProfileResponse)
def get_cv_by_id(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a saved CV profile by database ID (must belong to current user)."""
    return cv_to_response(get_cv_for_user(db, current_user, cv_id))
