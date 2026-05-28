"""Shared schema types."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class SkillConfidence(BaseModel):
    skill: str
    confidence: float
    method: str = "exact"


class ExtractionDebug(BaseModel):
    """Pipeline debug snapshot — temporary aid for verifying extraction end-to-end."""

    scan_text_len: int = 0
    raw_regex: list[str] = Field(default_factory=list)
    raw_keyword: list[str] = Field(default_factory=list)
    raw_fuzzy: list[str] = Field(default_factory=list)
    raw_semantic: list[str] = Field(default_factory=list)
    raw_heuristic: list[str] = Field(default_factory=list)
    merged: list[str] = Field(default_factory=list)
    heuristic_merged: list[str] = Field(default_factory=list)
    merged_skills: list[str] = Field(default_factory=list)
    filtered_out: list[str] = Field(default_factory=list)
    priority_missing: list[str] = Field(default_factory=list)
    skills_confidence: list[SkillConfidence] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    skills: float = 0.0
    semantic: float = 0.0
    semantic_skills: float = 0.0
    embedding: float = 0.0
    title: float = 0.0
    experience: float = 0.0
    domain: float = 0.0


class JobSkillsDebug(BaseModel):
    scan_text_len: int = 0
    scan_preview: str = ""
    raw_regex: list[str] = Field(default_factory=list)
    raw_keyword: list[str] = Field(default_factory=list)
    raw_semantic: list[str] = Field(default_factory=list)
    title_inferred: list[str] = Field(default_factory=list)
    final_skills: list[str] = Field(default_factory=list)


class CVProfileBase(BaseModel):
    full_name: str | None = None
    email: str | None = None
    summary: str | None = None
    years_experience: int | None = None
    job_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    language: str = "en"
    is_demo: bool = False


class CVProfileResponse(CVProfileBase):
    id: int
    source_filename: str | None = None
    extraction_method: str = "mock_heuristic"
    skills_confidence: list[SkillConfidence] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    category: str
    employment_type: str
    salary_range: str | None = None
    url: str | None = None
    language: str = "en"
    is_demo: bool = False
    source: str = "seed"
    work_mode: str | None = None
    is_israel: bool = True
    location_tag: str | None = None
    posted_at: datetime

    model_config = {"from_attributes": True}


class JobSourceStats(BaseModel):
    name: str
    boards: list[str] = Field(default_factory=list)
    fetched: int = 0
    matched: int = 0
    israel: int = 0
    excluded: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    tagged: int = 0
    errors: list[str] = Field(default_factory=list)


class JobRefreshResponse(BaseModel):
    total_fetched: int
    total_israel: int
    total_excluded: int
    total_matched: int
    total_created: int
    total_updated: int
    total_skipped: int = 0
    total_tagged: int = 0
    duration_ms: int = 0
    success: bool = True
    partial: bool = False
    log_id: int | None = None
    sources: list[JobSourceStats]
    errors: list[str] = Field(default_factory=list)
    message: str = "Jobs refreshed from external boards."


class JobSearchResponse(BaseModel):
    items: list[JobResponse]
    total: int
    query: str | None = None


class JobCollectorLogResponse(BaseModel):
    id: int
    status: str
    sources: list[str] = Field(default_factory=list)
    total_fetched: int = 0
    total_matched: int = 0
    total_created: int = 0
    total_updated: int = 0
    total_skipped: int = 0
    duration_ms: int | None = None
    errors: list[str] = Field(default_factory=list)
    message: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class JobMatchResponse(BaseModel):
    id: int
    cv_profile_id: int
    job_id: int
    match_score: float
    match_reason: str
    missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    semantic_matches: list[str] = Field(default_factory=list)
    job_skills_extracted: list[str] = Field(default_factory=list)
    job_skills_debug: JobSkillsDebug | None = None
    score_breakdown: ScoreBreakdown | None = None
    semantic_overlap: float = 0.0
    created_at: datetime
    job: JobResponse | None = None

    model_config = {"from_attributes": True}


class CVUploadResponse(BaseModel):
    """Returned by POST /api/cv/upload — extracted profile plus matched jobs."""

    cv_profile: CVProfileResponse
    matches: list[JobMatchResponse]
    total_jobs_scored: int
    extraction_method: str = "mock_heuristic"
    skills_confidence: list[SkillConfidence] = Field(default_factory=list)
    extraction_debug: ExtractionDebug | None = None
    raw_text_preview: str | None = None
    message: str = "CV uploaded and matched successfully."
    partial_matches: bool = False
    match_warning: str | None = None
    jobs_count: int = 0
    matches_created: int = 0
    top_score: float | None = None


class UserSettingsResponse(BaseModel):
    id: int
    email: str
    daily_digest_enabled: bool
    digest_hour: int
    ui_language: str
    min_match_score: int
    preferred_job_keywords: list[str] = Field(default_factory=list)
    last_digest_sent_at: datetime | None = None
    demo_mode: bool
    include_saved_jobs: bool = False

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    email: str | None = None
    daily_digest_enabled: bool | None = None
    digest_hour: int | None = Field(None, ge=0, le=23)
    ui_language: str | None = None
    min_match_score: int | None = Field(None, ge=0, le=100)
    preferred_job_keywords: list[str] | None = None
    demo_mode: bool | None = None
    include_saved_jobs: bool | None = None


class EmailStatusResponse(BaseModel):
    smtp_configured: bool
    daily_email_enabled: bool
    from_address: str


class EmailLogResponse(BaseModel):
    id: int
    recipient: str
    subject: str
    match_count: int
    sent: bool
    preview_only: bool
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SchedulerLogResponse(BaseModel):
    id: int
    job_name: str
    status: str
    message: str
    match_count: int
    sent: bool
    preview_only: bool
    duration_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_jobs: int
    matched_jobs: int
    avg_match_score: float
    top_missing_skills: list[str]
    strongest_skills: list[str] = Field(default_factory=list)
    top_companies: list["CompanyMatchStat"] = Field(default_factory=list)
    role_distribution: list["CategoryMatchStat"] = Field(default_factory=list)
    cv_profile_id: int | None = None
    demo_mode: bool = False


class CompanyMatchStat(BaseModel):
    company: str
    count: int
    avg_score: float


class CategoryMatchStat(BaseModel):
    category: str
    count: int
    avg_score: float


class SkillInsight(BaseModel):
    skill: str
    count: int
    in_cv: bool = True


class CVInsightsResponse(BaseModel):
    cv_profile_id: int | None = None
    strongest_skills: list[SkillInsight] = Field(default_factory=list)
    missing_high_value_skills: list[SkillInsight] = Field(default_factory=list)
    recommended_learning: list[str] = Field(default_factory=list)
    career_recommendations: list[str] = Field(default_factory=list)


class SavedJobResponse(BaseModel):
    id: int
    job_id: int
    created_at: datetime
    job: JobResponse | None = None

    model_config = {"from_attributes": True}


class MatchRequest(BaseModel):
    cv_profile_id: int | None = None
    min_score: int = 0


class CVExtractResponse(CVProfileBase):
    """Structured fields returned by POST /api/cv/extract (may not be saved yet)."""

    id: int | None = None
    source_filename: str | None = None
    created_at: datetime | None = None
    extraction_method: str = "mock_heuristic"
    skills_confidence: list[SkillConfidence] = Field(default_factory=list)
    extraction_debug: ExtractionDebug | None = None
    raw_text_preview: str | None = None


class CalculateMatchRequest(BaseModel):
    """Body for POST /api/matches/calculate."""

    cv_profile_id: int
    min_score: float = Field(0, ge=0, le=100)
    job_ids: list[int] | None = Field(None, description="Optional subset of job IDs to score")
    use_live_ai: bool = Field(False, description="Attempt OpenAI/Gemini if configured")
    israel_only: bool = Field(True, description="Score only Israeli jobs (default)")


class CalculateMatchResponse(BaseModel):
    cv_profile_id: int
    matches: list[JobMatchResponse]
    total_scored: int
    scoring_method: str = "mock_heuristic"


class EmailDigestResponse(BaseModel):
    """Response from daily email / test digest endpoint."""

    sent: bool
    message: str
    count: int = 0
    preview: str | None = None
    html_preview: str | None = None
    preview_only: bool = False
    last_sent_at: datetime | None = None


class DemoActivateResponse(BaseModel):
    cv_profile: CVProfileResponse
    matches: list[JobMatchResponse]
    stats: DashboardStats
    message: str
