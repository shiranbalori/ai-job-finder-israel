"""Dashboard statistics aggregation."""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user_settings import UserSettings
from app.schemas.common import CategoryMatchStat, CompanyMatchStat, DashboardStats
from app.utils.json_helpers import from_json_list
from app.utils.skill_label import clean_skill_label, is_valid_skill_label


def build_dashboard_stats(
    db: Session,
    cv_profile_id: int | None = None,
    israel_only: bool = True,
) -> DashboardStats:
    if not cv_profile_id:
        cv = db.query(CVProfile).order_by(CVProfile.created_at.desc()).first()
        cv_profile_id = cv.id if cv else None

    jobs_q = db.query(Job).filter(Job.is_active == True)  # noqa: E712
    if israel_only:
        jobs_q = jobs_q.filter(Job.is_israel == True)  # noqa: E712
    total_jobs = jobs_q.count()

    q = db.query(JobMatch).options(joinedload(JobMatch.job))
    if cv_profile_id:
        q = q.filter(JobMatch.cv_profile_id == cv_profile_id)
    if israel_only:
        q = q.join(Job).filter(Job.is_israel == True)  # noqa: E712
    matches = q.all()
    scores = [m.match_score for m in matches]
    avg = sum(scores) / len(scores) if scores else 0.0

    missing_counter: Counter[str] = Counter()
    matched_counter: Counter[str] = Counter()
    company_scores: dict[str, list[float]] = defaultdict(list)
    category_scores: dict[str, list[float]] = defaultdict(list)

    for m in matches:
        for raw in from_json_list(m.missing_skills_json):
            cleaned = clean_skill_label(raw)
            if is_valid_skill_label(cleaned):
                missing_counter[cleaned] += 1
        for raw in from_json_list(m.matched_skills_json):
            cleaned = clean_skill_label(raw)
            if cleaned:
                matched_counter[cleaned] += 1
        if m.job:
            company_scores[m.job.company].append(m.match_score)
            category_scores[m.job.category].append(m.match_score)

    settings = db.query(UserSettings).first()

    top_companies = [
        CompanyMatchStat(
            company=company,
            count=len(vals),
            avg_score=round(sum(vals) / len(vals), 1),
        )
        for company, vals in sorted(
            company_scores.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True
        )[:5]
    ]

    role_distribution = [
        CategoryMatchStat(
            category=cat,
            count=len(vals),
            avg_score=round(sum(vals) / len(vals), 1),
        )
        for cat, vals in sorted(category_scores.items(), key=lambda x: len(x[1]), reverse=True)
    ]

    return DashboardStats(
        total_jobs=total_jobs,
        matched_jobs=len(matches),
        avg_match_score=round(avg, 1),
        top_missing_skills=[s for s, _ in missing_counter.most_common(5)],
        strongest_skills=[s for s, _ in matched_counter.most_common(6)],
        top_companies=top_companies,
        role_distribution=role_distribution,
        cv_profile_id=cv_profile_id,
        demo_mode=settings.demo_mode if settings else False,
    )
