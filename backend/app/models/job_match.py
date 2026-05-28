"""CV-to-job match results."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_profile_id: Mapped[int] = mapped_column(ForeignKey("cv_profiles.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    match_reason: Mapped[str] = mapped_column(Text, default="")
    missing_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    matched_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    semantic_matches_json: Mapped[str] = mapped_column(Text, default="[]")
    score_breakdown_json: Mapped[str] = mapped_column(Text, default="{}")
    job_skills_debug_json: Mapped[str] = mapped_column(Text, default="{}")
    semantic_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cv_profile: Mapped["CVProfile"] = relationship("CVProfile", back_populates="matches")
    job: Mapped["Job"] = relationship("Job", back_populates="matches")
