"""Normalized job record from external job board adapters."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FetchedJobDTO:
    """Provider-agnostic job before persistence."""

    external_id: str
    source: str  # greenhouse | lever | remoteok
    title: str
    company: str
    location: str
    description: str
    category: str
    work_mode: str  # remote | hybrid | onsite
    is_israel: bool = True
    location_tag: str = "israel"  # israel | remote_israel | hybrid
    url: str | None = None
    requirements: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    employment_type: str = "Full-time"
    language: str = "en"
    posted_at: datetime | None = None
