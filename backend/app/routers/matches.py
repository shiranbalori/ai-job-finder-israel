"""
Match scoring endpoints — calculate and retrieve CV-to-job matches.

| Method | Path                        | Description              |
|--------|-----------------------------|--------------------------|
| POST   | /api/matches/calculate      | **Calculate match scores**|
| GET    | /api/matches                | List saved matches       |
| GET    | /api/matches/stats/dashboard| Dashboard aggregates     |
| GET    | /api/matches/{match_id}     | Single match record      |
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.job_match import JobMatch
from app.models.user import User
from app.schemas.common import (
    CalculateMatchRequest,
    CalculateMatchResponse,
    DashboardStats,
    JobMatchResponse,
)
from app.services.cv_service import get_cv_or_404
from app.services.match_service import calculate_matches, list_saved_matches
from app.services.stats import build_dashboard_stats
from app.services.user_data import get_cv_for_user, get_user_latest_cv

from app.utils.serializers import match_to_response

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _resolve_cv_id(db: Session, user: User, cv_profile_id: int | None) -> int | None:
    if cv_profile_id:
        return get_cv_for_user(db, user, cv_profile_id).id
    cv = get_user_latest_cv(db, user)
    return cv.id if cv else None


@router.post("/calculate", response_model=CalculateMatchResponse)
async def calculate_match_scores(
    body: CalculateMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Calculate match score** (0–100) for each active job against a saved CV profile.

    Uses mock AI heuristics by default (skill overlap + experience bonus).
    Results are persisted in the `job_matches` table.
    """
    cv = get_cv_for_user(db, current_user, body.cv_profile_id)
    match_result = await calculate_matches(
        db,
        cv,
        min_score=body.min_score,
        job_ids=body.job_ids,
        use_live_ai=body.use_live_ai,
        israel_only=body.israel_only,
        fast=not body.use_live_ai,
    )
    settings = get_settings()
    method = "live_ai" if body.use_live_ai and settings.ai_provider != "mock" else "mock_heuristic"

    return CalculateMatchResponse(
        cv_profile_id=cv.id,
        matches=[match_to_response(m) for m in match_result.matches],
        total_scored=match_result.jobs_scored,
        scoring_method=method,
    )


@router.get("", response_model=list[JobMatchResponse])
def list_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cv_profile_id: int | None = None,
    min_score: float = Query(0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=100),
    israel_only: bool = Query(True, description="Return matches for Israeli jobs only"),
    sort_by: str = Query(
        "score",
        pattern="^(score|newest|semantic)$",
        description="Sort: score | newest | semantic",
    ),
):
    """Return previously calculated matches for the authenticated user."""
    resolved_cv = _resolve_cv_id(db, current_user, cv_profile_id)
    matches = list_saved_matches(
        db,
        cv_profile_id=resolved_cv,
        min_score=min_score,
        limit=limit,
        israel_only=israel_only,
        sort_by=sort_by,
    )
    return [match_to_response(m) for m in matches]


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cv_profile_id: int | None = None,
    israel_only: bool = Query(True),
):
    """Aggregate stats for the dashboard UI."""
    resolved_cv = _resolve_cv_id(db, current_user, cv_profile_id)
    return build_dashboard_stats(db, resolved_cv, israel_only=israel_only)


@router.get("/{match_id}", response_model=JobMatchResponse)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one saved match including embedded job details."""
    match = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(JobMatch.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")
    get_cv_for_user(db, current_user, match.cv_profile_id)
    return match_to_response(match)
