"""Per-user data access helpers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cv_profile import CVProfile
from app.models.user import User
from app.models.user_settings import UserSettings


def get_user_settings(db: Session, user: User) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings:
        return settings
    settings = UserSettings(user_id=user.id, email=user.email)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def get_user_latest_cv(db: Session, user: User, *, include_demo: bool = True) -> CVProfile | None:
    q = db.query(CVProfile).filter(CVProfile.user_id == user.id)
    if not include_demo:
        q = q.filter(CVProfile.is_demo == False)  # noqa: E712
    return q.order_by(CVProfile.created_at.desc()).first()


def get_cv_for_user(db: Session, user: User, cv_id: int) -> CVProfile:
    cv = db.query(CVProfile).filter(CVProfile.id == cv_id, CVProfile.user_id == user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV profile not found.")
    return cv
