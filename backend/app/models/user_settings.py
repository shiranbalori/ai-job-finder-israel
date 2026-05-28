"""User preferences for email digest and UI."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(200), default="demo@example.com")
    daily_digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    digest_hour: Mapped[int] = mapped_column(Integer, default=8)
    ui_language: Mapped[str] = mapped_column(String(10), default="en")
    min_match_score: Mapped[int] = mapped_column(Integer, default=50)
    preferred_job_keywords_json: Mapped[str] = mapped_column(Text, default="[]")
    last_digest_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    demo_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    include_saved_jobs: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User | None"] = relationship("User", back_populates="settings")
