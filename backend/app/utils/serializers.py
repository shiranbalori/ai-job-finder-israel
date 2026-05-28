"""Convert ORM models to Pydantic response schemas."""

import json

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.common import CVProfileResponse, JobMatchResponse, JobResponse, JobSkillsDebug, ScoreBreakdown, SkillConfidence
from app.utils.json_helpers import from_json_list


def _parse_skills_confidence(raw: str) -> list[SkillConfidence]:
    try:
        items = json.loads(raw or "[]")
        return [SkillConfidence(**item) for item in items if isinstance(item, dict) and item.get("skill")]
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def _parse_score_breakdown(raw: str) -> ScoreBreakdown | None:
    try:
        data = json.loads(raw or "{}")
        if not data:
            return None
        return ScoreBreakdown(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def cv_to_response(cv: CVProfile) -> CVProfileResponse:
    return CVProfileResponse(
        id=cv.id,
        full_name=cv.full_name,
        email=cv.email,
        summary=cv.summary,
        years_experience=cv.years_experience,
        job_titles=from_json_list(cv.job_titles_json),
        skills=from_json_list(cv.skills_json),
        tools=from_json_list(cv.tools_json),
        technologies=from_json_list(cv.technologies_json),
        languages=from_json_list(cv.languages_json),
        language=cv.language,
        is_demo=cv.is_demo,
        source_filename=cv.source_filename,
        extraction_method=cv.extraction_method or "mock_heuristic",
        skills_confidence=_parse_skills_confidence(getattr(cv, "skills_confidence_json", "[]")),
        created_at=cv.created_at,
    )


def job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        requirements=from_json_list(job.requirements_json),
        skills=from_json_list(job.skills_json),
        tags=from_json_list(getattr(job, "tags_json", "[]")),
        category=job.category,
        employment_type=job.employment_type,
        salary_range=job.salary_range,
        url=job.url,
        language=job.language,
        is_demo=job.is_demo,
        source=job.source or "seed",
        work_mode=job.work_mode,
        is_israel=job.is_israel,
        location_tag=job.location_tag,
        posted_at=job.posted_at,
    )


def _parse_job_skills_debug(raw: str) -> JobSkillsDebug | None:
    try:
        data = json.loads(raw or "{}")
        if not data:
            return None
        return JobSkillsDebug(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def match_to_response(match: JobMatch, include_job: bool = True) -> JobMatchResponse:
    job_debug_raw = json.loads(getattr(match, "job_skills_debug_json", "{}") or "{}")
    return JobMatchResponse(
        id=match.id,
        cv_profile_id=match.cv_profile_id,
        job_id=match.job_id,
        match_score=match.match_score,
        match_reason=match.match_reason,
        missing_skills=from_json_list(match.missing_skills_json),
        matched_skills=from_json_list(match.matched_skills_json),
        semantic_matches=from_json_list(getattr(match, "semantic_matches_json", "[]")),
        job_skills_extracted=job_debug_raw.get("final_skills", []) if job_debug_raw else [],
        job_skills_debug=_parse_job_skills_debug(getattr(match, "job_skills_debug_json", "{}")),
        score_breakdown=_parse_score_breakdown(getattr(match, "score_breakdown_json", "{}")),
        semantic_overlap=float(getattr(match, "semantic_overlap", 0) or 0),
        created_at=match.created_at,
        job=job_to_response(match.job) if include_job and match.job else None,
    )
