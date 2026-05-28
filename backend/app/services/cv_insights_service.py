"""Aggregate CV-level insights from profile + match history."""

from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session, joinedload

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.common import CVInsightsResponse, SkillInsight
from app.utils.json_helpers import from_json_list


def _latest_cv(db: Session, cv_profile_id: int | None) -> CVProfile | None:
    if cv_profile_id:
        return db.query(CVProfile).filter(CVProfile.id == cv_profile_id).first()
    return db.query(CVProfile).order_by(CVProfile.created_at.desc()).first()


def build_cv_insights(
    db: Session,
    cv_profile_id: int | None = None,
    *,
    israel_only: bool = True,
) -> CVInsightsResponse:
    cv = _latest_cv(db, cv_profile_id)
    if not cv:
        return CVInsightsResponse(cv_profile_id=None)

    q = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job))
        .filter(JobMatch.cv_profile_id == cv.id)
    )
    if israel_only:
        q = q.join(Job).filter(Job.is_israel == True)  # noqa: E712
    matches = q.all()

    matched_counter: Counter[str] = Counter()
    missing_counter: Counter[str] = Counter()
    for m in matches:
        matched_counter.update(from_json_list(m.matched_skills_json))
        missing_counter.update(from_json_list(m.missing_skills_json))

    cv_skills = set(from_json_list(cv.skills_json))
    strongest = [
        SkillInsight(skill=s, count=c, in_cv=s in cv_skills)
        for s, c in matched_counter.most_common(8)
    ]

    high_value_missing = [
        SkillInsight(skill=s, count=c, in_cv=s in cv_skills)
        for s, c in missing_counter.most_common(8)
    ]

    learning_areas: list[str] = []
    for item in high_value_missing[:5]:
        if not item.in_cv:
            learning_areas.append(item.skill)

    recommendations: list[str] = []
    scores = [m.match_score for m in matches]
    avg = sum(scores) / len(scores) if scores else 0.0
    top_cats = Counter(m.job.category for m in matches if m.job).most_common(2)

    if avg >= 75:
        recommendations.append(
            "Your profile aligns strongly with AI roles — prioritize senior or lead positions."
        )
    elif avg >= 55:
        recommendations.append(
            "Solid fit for applied AI roles — highlight production projects and measurable impact."
        )
    else:
        recommendations.append(
            "Focus on closing top skill gaps to unlock more AI Engineer matches."
        )

    if top_cats:
        cat_names = ", ".join(c for c, _ in top_cats)
        recommendations.append(f"Best-fit categories right now: {cat_names}.")

    if learning_areas:
        recommendations.append(
            f"Upskilling in {', '.join(learning_areas[:3])} would unlock more high-score matches."
        )

    return CVInsightsResponse(
        cv_profile_id=cv.id,
        strongest_skills=strongest,
        missing_high_value_skills=high_value_missing,
        recommended_learning=learning_areas[:6],
        career_recommendations=recommendations[:4],
    )
