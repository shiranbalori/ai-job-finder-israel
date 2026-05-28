"""Job listing model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200), default="Israel")
    description: Mapped[str] = mapped_column(Text)
    requirements_json: Mapped[str] = mapped_column(Text, default="[]")
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    parsed_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    skills_content_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    embedding_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="AI / Data")
    employment_type: Mapped[str] = mapped_column(String(50), default="Full-time")
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(50), default="seed", index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    work_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_israel: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    location_tag: Mapped[str | None] = mapped_column(String(30), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches: Mapped[list["JobMatch"]] = relationship("JobMatch", back_populates="job")
