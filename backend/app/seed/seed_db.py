"""Populate SQLite with demo jobs and default settings."""

from sqlalchemy.orm import Session

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.models.user_settings import UserSettings
from app.seed.demo_data import DEMO_CV, DEMO_JOBS
from app.services.job_filter import classify_job_location
from app.utils.json_helpers import to_json_list


def seed_jobs(db: Session, force: bool = False) -> int:
    """Insert mock Israeli AI/Data jobs if table is empty."""
    count = db.query(Job).count()
    if count > 0 and not force:
        return count

    if force:
        db.query(Job).filter(Job.is_demo == True).delete()  # noqa: E712

    for data in DEMO_JOBS:
        location = data["location"]
        _, location_tag = classify_job_location(location)
        if not location_tag:
            location_tag = "hybrid" if "hybrid" in location.lower() else "israel"
        job = Job(
            title=data["title"],
            company=data["company"],
            location=location,
            description=data["description"],
            requirements_json=to_json_list(data["requirements"]),
            skills_json=to_json_list(data["skills"]),
            category=data["category"],
            employment_type=data["employment_type"],
            salary_range=data.get("salary_range"),
            url=data.get("url"),
            language=data.get("language", "en"),
            source="seed",
            external_id=f"seed:{data['company']}:{data['title']}"[:200],
            work_mode=data.get("work_mode", location_tag if location_tag != "israel" else "onsite"),
            is_israel=True,
            location_tag=location_tag,
            is_demo=True,
            is_active=True,
        )
        db.add(job)
    db.commit()
    return db.query(Job).count()


def seed_settings(db: Session) -> UserSettings:
    settings = db.query(UserSettings).first()
    if settings:
        return settings
    settings = UserSettings(
        email="demo@example.com",
        daily_digest_enabled=False,
        digest_hour=8,
        ui_language="en",
        min_match_score=50,
        demo_mode=False,
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def create_demo_cv(db: Session) -> CVProfile:
    """Create or return the demo CV profile."""
    existing = db.query(CVProfile).filter(CVProfile.is_demo == True).first()  # noqa: E712
    if existing:
        return existing

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
