"""
Full Demo Mode service — curated CV, jobs, and match narratives.

Works without OpenAI/Gemini API keys or real CV uploads.
Designed for interview demos with stable, impressive match results.
"""

import json

from sqlalchemy.orm import Session, joinedload

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user_settings import UserSettings
from app.seed.demo_data import DEMO_CURATED_MATCHES, DEMO_CV
from app.seed.seed_db import seed_jobs, seed_settings
from app.services.mock_ai import mock_match_job
from app.services.stats import build_dashboard_stats
from app.utils.json_helpers import to_json_list
from app.utils.serializers import cv_to_response, match_to_response


def get_or_refresh_demo_cv(db: Session) -> CVProfile:
    """Return demo CV profile, refreshing fields from seed data each activation."""
    cv = db.query(CVProfile).filter(CVProfile.is_demo == True).first()  # noqa: E712
    if cv:
        cv.full_name = DEMO_CV["full_name"]
        cv.email = DEMO_CV["email"]
        cv.summary = DEMO_CV["summary"]
        cv.years_experience = DEMO_CV["years_experience"]
        cv.job_titles_json = to_json_list(DEMO_CV["job_titles"])
        cv.skills_json = to_json_list(DEMO_CV["skills"])
        cv.tools_json = to_json_list(DEMO_CV["tools"])
        cv.technologies_json = to_json_list(DEMO_CV["technologies"])
        cv.raw_text = DEMO_CV["raw_text"]
        cv.source_filename = DEMO_CV["source_filename"]
        cv.language = DEMO_CV["language"]
        db.commit()
        db.refresh(cv)
        return cv

    cv = CVProfile(
        full_name=DEMO_CV["full_name"],
        email=DEMO_CV["email"],
        summary=DEMO_CV["summary"],
        years_experience=DEMO_CV["years_experience"],
        job_titles_json=to_json_list(DEMO_CV["job_titles"]),
        skills_json=to_json_list(DEMO_CV["skills"]),
        tools_json=to_json_list(DEMO_CV["tools"]),
        technologies_json=to_json_list(DEMO_CV["technologies"]),
        raw_text=DEMO_CV["raw_text"],
        source_filename=DEMO_CV["source_filename"],
        is_demo=True,
        language=DEMO_CV["language"],
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def apply_curated_demo_matches(db: Session, cv: CVProfile, jobs: list[Job]) -> list[JobMatch]:
    """
    Score demo jobs using curated narratives when available, heuristic fallback otherwise.
    Persists to job_matches and returns sorted list (highest score first).
    """
    db.query(JobMatch).filter(JobMatch.cv_profile_id == cv.id).delete()

    results: list[JobMatch] = []
    for job in jobs:
        if not job.is_active:
            continue

        curated = DEMO_CURATED_MATCHES.get(job.company)
        if curated:
            payload = curated
        else:
            payload = mock_match_job(cv, job)

        match = JobMatch(
            cv_profile_id=cv.id,
            job_id=job.id,
            match_score=float(payload["match_score"]),
            match_reason=str(payload["match_reason"]),
            missing_skills_json=to_json_list(payload.get("missing_skills", [])),
            matched_skills_json=to_json_list(payload.get("matched_skills", [])),
            semantic_matches_json=to_json_list(payload.get("semantic_matches", [])),
            score_breakdown_json=json.dumps(payload.get("score_breakdown") or {}),
            job_skills_debug_json=json.dumps(payload.get("job_skills_debug") or {}),
            semantic_overlap=float(payload.get("semantic_overlap", 0) or 0),
        )
        db.add(match)
        results.append(match)

    db.commit()
    for m in results:
        db.refresh(m)

    return sorted(results, key=lambda x: x.match_score, reverse=True)


def activate_full_demo(db: Session) -> dict:
    """
    One-click demo: seed jobs, load fake CV, compute curated matches, enable demo flag.
    """
    seed_jobs(db)
    seed_settings(db)
    cv = get_or_refresh_demo_cv(db)

    jobs = db.query(Job).filter(Job.is_active == True, Job.is_demo == True).all()  # noqa: E712
    apply_curated_demo_matches(db, cv, jobs)

    settings = db.query(UserSettings).first()
    if settings:
        settings.demo_mode = True
        db.commit()

    matches = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(JobMatch.cv_profile_id == cv.id)
        .order_by(JobMatch.match_score.desc())
        .all()
    )

    stats = build_dashboard_stats(db, cv_profile_id=cv.id)
    stats.demo_mode = True

    return {
        "cv_profile": cv_to_response(cv),
        "matches": [match_to_response(m) for m in matches],
        "stats": stats,
        "jobs_count": len(jobs),
        "message": "Demo mode active — view sample AI job matches across Israeli AI/Data roles.",
    }
